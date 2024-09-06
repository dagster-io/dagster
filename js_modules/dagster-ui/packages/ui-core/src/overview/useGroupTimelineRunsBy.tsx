import {useCallback, useMemo} from 'react';

import {useQueryAndLocalStoragePersistedState} from '../hooks/useQueryAndLocalStoragePersistedState';

const GROUP_BY_KEY = 'dagster.run-timeline-group-by';

export type GroupRunsBy = 'job' | 'automation';

export const useGroupTimelineRunsBy = (
  defaultValue: GroupRunsBy = 'job',
): [GroupRunsBy, (value: GroupRunsBy) => void] => {
  const validate = useCallback(
    (value: string) => {
      switch (value) {
        case 'job':
        case 'automation':
          return value;
        default:
          return defaultValue;
      }
    },
    [defaultValue],
  );

  const [groupRunsBy, setGroupRunsBy] = useQueryAndLocalStoragePersistedState<GroupRunsBy>({
    localStorageKey: GROUP_BY_KEY,
    queryKey: 'groupBy',
    encode: (value) => {
      return {groupBy: value};
    },
    decode: (pair) => {
      return validate(pair.groupBy);
    },
    isEmptyState: (value) => !value,
  });

  const setGroupByWithDefault = useCallback(
    (value: GroupRunsBy) => {
      setGroupRunsBy(value || defaultValue);
    },
    [defaultValue, setGroupRunsBy],
  );

  return useMemo(() => [groupRunsBy, setGroupByWithDefault], [groupRunsBy, setGroupByWithDefault]);
};
