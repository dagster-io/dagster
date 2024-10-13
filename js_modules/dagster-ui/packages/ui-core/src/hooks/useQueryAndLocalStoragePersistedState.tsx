import * as React from 'react';

import {QueryPersistedDataType, useQueryPersistedState} from './useQueryPersistedState';
import {useSetStateUpdateCallback} from './useSetStateUpdateCallback';

/**
 *
 * Use URL query string as main source of truth with localStorage as the backup if no state is found in the query string
 * Syncs changes back to localStorage but relies solely on queryString after the initial render
 * @returns
 */
export const useQueryAndLocalStoragePersistedState = <T extends QueryPersistedDataType>(
  props: Parameters<typeof useQueryPersistedState<T>>[0] & {
    localStorageKey: string;
    isEmptyState: (state: T) => boolean;
  },
): [T, (setterOrState: React.SetStateAction<T>) => void] => {
  // Grab state from localStorage as "initialState"
  const initialState = React.useMemo(() => {
    try {
      const value = localStorage.getItem(props.localStorageKey);
      if (value) {
        return props.decode?.(JSON.parse(value));
      }
    } catch {}
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.localStorageKey]);

  const [state, setter] = useQueryPersistedState(props);

  const isFirstRender = React.useRef(true);
  React.useEffect(() => {
    if (initialState && props.isEmptyState(state)) {
      setter(initialState);
    }
    isFirstRender.current = false;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return [
    isFirstRender.current && initialState && props.isEmptyState(state) ? initialState : state,
    useSetStateUpdateCallback(state, (nextState) => {
      setter(nextState);

      // Persist state updates to localStorage
      window.localStorage.setItem(
        props.localStorageKey,
        JSON.stringify(props.encode ? props.encode(nextState) : nextState),
      );
    }),
  ];
};
