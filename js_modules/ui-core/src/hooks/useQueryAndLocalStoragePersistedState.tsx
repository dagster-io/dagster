import * as React from 'react';

import {QueryPersistedDataType, useQueryPersistedState} from './useQueryPersistedState';
import {useSetStateUpdateCallback} from './useSetStateUpdateCallback';
import {useStateWithStorage} from './useStateWithStorage';

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
  const {localStorageKey, isEmptyState, decode, encode} = props;

  const decoder = React.useCallback((json: any) => (decode ? decode(json ?? {}) : json), [decode]);

  const [valueFromLocalStorage, setValueFromLocalStorage] = useStateWithStorage(
    localStorageKey,
    decoder,
  );

  const [state, setter] = useQueryPersistedState(props);

  return [
    isEmptyState(state) ? (valueFromLocalStorage ?? state) : state,
    useSetStateUpdateCallback(state, (nextState) => {
      setValueFromLocalStorage(encode ? encode(nextState) : nextState);
      setter(nextState);
    }),
  ];
};
