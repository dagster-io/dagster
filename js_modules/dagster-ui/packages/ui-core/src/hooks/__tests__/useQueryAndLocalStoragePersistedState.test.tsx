import {act, renderHook, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {Route} from '../../app/Route';
import {useQueryAndLocalStoragePersistedState} from '../useQueryAndLocalStoragePersistedState';

// Mock local storage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useQueryAndLocalStoragePersistedState', () => {
  afterEach(() => {
    localStorageMock.clear();
  });

  test('persists state to localStorage and loads initial state from local storage', async () => {
    let querySearch: string | undefined;

    const localStorageKey = 'asset-graph-open-nodes';

    localStorageMock.setItem(localStorageKey, JSON.stringify({'open-nodes': ['test']}));

    const hookResult = renderHook(
      () =>
        useQueryAndLocalStoragePersistedState<Set<string>>({
          localStorageKey: 'asset-graph-open-nodes',
          encode: (val) => {
            return {'open-nodes': Array.from(val)};
          },
          decode: (qs) => {
            return new Set(qs['open-nodes']);
          },
          isEmptyState: (val) => val.size === 0,
        }),
      {
        wrapper: ({children}: {children?: React.ReactNode}) => {
          return (
            <MemoryRouter initialEntries={['/foo/hello']}>
              {children}
              <Route
                path="*"
                render={({location}) => (querySearch = location.search) && <span />}
              />
            </MemoryRouter>
          );
        },
      } as any,
    );

    let state, setter: any;

    [state, setter] = hookResult.result.current;

    // Assert that the state was retrieved from local storage
    expect(localStorageMock.getItem(localStorageKey)).toEqual(
      JSON.stringify({'open-nodes': ['test']}),
    );

    expect(state).toEqual(new Set(['test']));

    act(() => {
      setter(new Set(['test', 'test2']));
    });

    [state, setter] = hookResult.result.current;

    expect(localStorageMock.getItem(localStorageKey)).toEqual(
      JSON.stringify({'open-nodes': ['test', 'test2']}),
    );

    expect(state).toEqual(new Set(['test', 'test2']));

    await waitFor(() => {
      expect(querySearch).toEqual('?open-nodes%5B%5D=test&open-nodes%5B%5D=test2');
    });
  });

  test('uses queryString as source of truth if query string is present and localStorage data is also present', async () => {
    const localStorageKey = 'asset-graph-open-nodes';

    localStorageMock.setItem(localStorageKey, JSON.stringify({'open-nodes': ['test']}));

    const hookResult = renderHook(
      () =>
        useQueryAndLocalStoragePersistedState<Set<string>>({
          localStorageKey: 'asset-graph-open-nodes',
          encode: (val) => {
            return {'open-nodes': Array.from(val)};
          },
          decode: (qs) => {
            return new Set(qs['open-nodes']);
          },
          isEmptyState: (val) => val.size === 0,
        }),
      {
        wrapper: ({children}: {children?: React.ReactNode}) => {
          return (
            <MemoryRouter
              initialEntries={[
                '/foo/hello?open-nodes%5B%5D=basic_assets_repository%40toys%3Abasic_assets',
              ]}
            >
              {children}
            </MemoryRouter>
          );
        },
      } as any,
    );

    const [state] = hookResult.result.current;

    // Assert that the state was retrieved from local storage
    expect(localStorageMock.getItem(localStorageKey)).toEqual(
      JSON.stringify({'open-nodes': ['test']}),
    );

    expect(state).toEqual(new Set(['basic_assets_repository@toys:basic_assets']));
  });
});
