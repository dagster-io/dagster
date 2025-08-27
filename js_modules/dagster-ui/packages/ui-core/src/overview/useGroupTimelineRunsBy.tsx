import {useCallback} from 'react';

import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

const GROUP_BY_KEY = 'dagster.run-timeline-group-by';

export type GroupRunsBy = 'job' | 'automation';

const validate = (value: string) => {
  switch (value) {
    case 'job':
    case 'automation':
      return value;
    default:
      return null;
  }
};

export const useGroupTimelineRunsBy = (
  defaultValue: GroupRunsBy = 'job',
): [GroupRunsBy, (value: GroupRunsBy) => void] => {
  const [storedValue, setStoredValue] = useStateWithStorage(GROUP_BY_KEY, validate);

  const [queryValue, setQueryValue] = useQueryPersistedState<GroupRunsBy | null>({
    queryKey: 'groupBy',
    encode: (value) => (value ? {groupBy: value} : {}),
    decode: (pair) => {
      if (typeof pair.groupBy === 'string') {
        const result = validate(pair.groupBy);
        if (result) {
          return result;
        }
      }
      return null;
    },
  });

  /**
   * If a query value is provided, use it without writing to localStorage.
   * Otherwise, if the user has a stored value (from previously choosing an option), use that.
   * If neither are provided, use the default value.
   */
  const outputValue = queryValue || storedValue || defaultValue;

  /**
   * Set the query parameter and write the preference to localStorage. This is used when
   * the user specifically chooses an option.
   */
  const setGroupByWithDefault = useCallback(
    (value: GroupRunsBy) => {
      setStoredValue(value);
      setQueryValue(value);
    },
    [setStoredValue, setQueryValue],
  );

  return [outputValue, setGroupByWithDefault];
};
