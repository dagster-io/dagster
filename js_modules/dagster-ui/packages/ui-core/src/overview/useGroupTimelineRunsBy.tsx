import {useCallback, useMemo} from 'react';
import {useHistory} from 'react-router-dom';

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

  const history = useHistory();
  const [groupRunsBy, setGroupRunsBy] = useStateWithStorage(storageKey, validate);
  const setGroupByWithDefault = useCallback(
    (value: GroupRunsBy) => {
      setGroupRunsBy(value || defaultValue);

      // Update URL with selected group by field
      const searchParams = new URLSearchParams(window.location.search);
      searchParams.set('groupBy', value || defaultValue);
      history.replace({search: searchParams.toString()});
    },
    [defaultValue, setGroupRunsBy, history],
  );

  return useMemo(() => [groupRunsBy, setGroupByWithDefault], [groupRunsBy, setGroupByWithDefault]);
};
