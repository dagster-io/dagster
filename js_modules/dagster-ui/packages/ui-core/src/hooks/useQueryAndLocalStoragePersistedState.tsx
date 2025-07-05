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
  const {localStorageKey, isEmptyState, decode} = props;

  const getInitialValueFromLocalStorage = React.useMemo(() => {
    let value: T | undefined;
    return () => {
      if (value !== undefined) {
        return value;
      }
      try {
        const item = window.localStorage.getItem(localStorageKey);
        if (item) {
          const parsed = JSON.parse(item);
          value = parsed;
          if (decode) {
            value = decode(parsed);
          }
          return value;
        }
      } catch (error) {
        console.error('Error reading from localStorage:', error);
      }
      return undefined;
    };
  }, [localStorageKey, decode]);

  const [state, setter] = useQueryPersistedState(props);

  return [
    isEmptyState(state) ? (getInitialValueFromLocalStorage() ?? state) : state,
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
