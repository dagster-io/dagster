import {act, renderHook} from '@testing-library/react';
import * as React from 'react';

import {AppContext} from '../../app/AppContext';
import {useRecentSelections} from '../useRecentSelections';

const wrapperWithPrefix = (localCacheIdPrefix: string) => {
  const Wrapper = ({children}: {children: React.ReactNode}) => (
    <AppContext.Provider
      value={{basePath: '', rootServerURI: '', telemetryEnabled: false, localCacheIdPrefix}}
    >
      {children}
    </AppContext.Provider>
  );
  return Wrapper;
};

describe('useRecentSelections', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('records selections newest-first', () => {
    const {result} = renderHook(() => useRecentSelections('test'));

    act(() => result.current.addRecentSelection('key:"a"'));
    act(() => result.current.addRecentSelection('key:"b"'));

    expect(result.current.recentSelections).toEqual(['key:"b"', 'key:"a"']);
  });

  it('moves a repeated selection back to the front instead of duplicating it', () => {
    const {result} = renderHook(() => useRecentSelections('test'));

    act(() => result.current.addRecentSelection('key:"a"'));
    act(() => result.current.addRecentSelection('key:"b"'));
    act(() => result.current.addRecentSelection('key:"a"'));

    expect(result.current.recentSelections).toEqual(['key:"a"', 'key:"b"']);
  });

  it('ignores empty and whitespace-only selections, and trims the rest', () => {
    const {result} = renderHook(() => useRecentSelections('test'));

    act(() => result.current.addRecentSelection(''));
    act(() => result.current.addRecentSelection('   '));
    act(() => result.current.addRecentSelection('  key:"a"  '));

    expect(result.current.recentSelections).toEqual(['key:"a"']);
  });

  it('caps the stored history', () => {
    const {result} = renderHook(() => useRecentSelections('test'));

    for (let i = 0; i < 15; i++) {
      act(() => result.current.addRecentSelection(`key:"${i}"`));
    }

    expect(result.current.recentSelections).toHaveLength(10);
    expect(result.current.recentSelections[0]).toEqual('key:"14"');
  });

  it('keeps separate histories per key', () => {
    const {result: assets} = renderHook(() => useRecentSelections('assets'));
    const {result: jobs} = renderHook(() => useRecentSelections('jobs'));

    act(() => assets.current.addRecentSelection('key:"a"'));

    expect(assets.current.recentSelections).toEqual(['key:"a"']);
    expect(jobs.current.recentSelections).toEqual([]);
  });

  it('shares history between inputs using the same key', () => {
    const {result: catalog} = renderHook(() => useRecentSelections('assets'));
    const {result: graph} = renderHook(() => useRecentSelections('assets'));

    act(() => catalog.current.addRecentSelection('key:"a"'));
    expect(graph.current.recentSelections).toEqual(['key:"a"']);

    act(() => graph.current.addRecentSelection('key:"b"'));
    expect(catalog.current.recentSelections).toEqual(['key:"b"', 'key:"a"']);
  });

  it('persists across remounts', () => {
    const {result, unmount} = renderHook(() => useRecentSelections('test'));
    act(() => result.current.addRecentSelection('key:"a"'));
    unmount();

    const {result: remounted} = renderHook(() => useRecentSelections('test'));
    expect(remounted.current.recentSelections).toEqual(['key:"a"']);
  });

  it('scopes storage by the deployment cache prefix', () => {
    const {result: deploymentA} = renderHook(() => useRecentSelections('assets'), {
      wrapper: wrapperWithPrefix('org/prod'),
    });
    const {result: deploymentB} = renderHook(() => useRecentSelections('assets'), {
      wrapper: wrapperWithPrefix('org/staging'),
    });

    act(() => deploymentA.current.addRecentSelection('key:"a"'));

    expect(deploymentA.current.recentSelections).toEqual(['key:"a"']);
    expect(deploymentB.current.recentSelections).toEqual([]);
  });

  it('does not record anything when no key is provided', () => {
    const {result} = renderHook(() => useRecentSelections(undefined));

    act(() => result.current.addRecentSelection('key:"a"'));

    expect(result.current.recentSelections).toEqual([]);
  });

  it('keeps identities stable across renders so consumers do not re-render', () => {
    const {result, rerender} = renderHook(() => useRecentSelections('test'));

    const firstSelections = result.current.recentSelections;
    const firstAdd = result.current.addRecentSelection;
    rerender();

    expect(result.current.recentSelections).toBe(firstSelections);
    expect(result.current.addRecentSelection).toBe(firstAdd);
  });

  describe('stored data from another build or tab', () => {
    const seed = (value: string) =>
      window.localStorage.setItem('undefined/recent-selections/test', value);

    const read = () =>
      renderHook(() => useRecentSelections('test')).result.current.recentSelections;

    it('ignores values that are not an array of strings', () => {
      seed('not json');
      expect(read()).toEqual([]);

      seed(JSON.stringify({a: 1}));
      expect(read()).toEqual([]);

      seed(JSON.stringify(['key:"a"', 5, null, 'key:"b"']));
      expect(read()).toEqual(['key:"a"', 'key:"b"']);
    });

    it('applies the dedupe, blank and cap rules on read', () => {
      seed(JSON.stringify(['key:"a"', 'key:"a"', '  ', 'key:"b"']));
      expect(read()).toEqual(['key:"a"', 'key:"b"']);

      seed(JSON.stringify(Array.from({length: 20}, (_, i) => `key:"${i}"`)));
      expect(read()).toHaveLength(10);
    });
  });
});
