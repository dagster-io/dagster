import {useCallback, useMemo} from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

const GROUP_BY_KEY = 'dagster.run-timeline-group-by';

export type GroupRunsBy = 'job' | 'automation';

export const useGroupTimelineRunsBy = (
  defaultValue: GroupRunsBy = 'job',
  storageKey = GROUP_BY_KEY,
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

  const [groupRunsBy, setGroupRunsBy] = useStateWithStorage(storageKey, validate);
  const setGroupByWithDefault = useCallback(
    (value: GroupRunsBy) => {
      setGroupRunsBy(value || defaultValue);
    },
    [defaultValue, setGroupRunsBy],
  );

  return useMemo(() => [groupRunsBy, setGroupByWithDefault], [groupRunsBy, setGroupByWithDefault]);
};
