import {act, renderHook, waitFor} from '@testing-library/react';
import React from 'react';
import {MemoryRouter, Route} from 'react-router-dom';

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

  test('persists state to localStorage', async () => {
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
      },
    );

    let state, setter: any;

    [state, setter] = hookResult.result.current;

    // Assert that the state was retrieved from local storage
    expect(localStorageMock.getItem(localStorageKey)).toEqual(
      JSON.stringify({'open-nodes': ['test']}),
    );

    expect(state).toEqual(new Set(['test']));

    act(() => {
      // Typescript doesnt realize the array being returned is a constant tuple and not an array that contains both state/setters
      // so cast this to any
      (setter as any)!(new Set(['test', 'test2']));
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
});
