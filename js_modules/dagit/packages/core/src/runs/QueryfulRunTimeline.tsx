import * as React from 'react';

import {RunsFilter} from '../types/globalTypes';

import {RunTimeline} from './RunTimeline';
import {useRunsForTimeline} from './useRunsForTimeline';

interface Props {
  range: [number, number];
  runsFilter?: RunsFilter;
  visibleJobKeys: Set<string>;
}

export const QueryfulRunTimeline = (props: Props) => {
  const {range, visibleJobKeys, runsFilter = {}} = props;
  const {jobs, loading} = useRunsForTimeline(range, runsFilter);

  const visibleJobs = React.useMemo(() => jobs.filter(({key}) => visibleJobKeys.has(key)), [
    jobs,
    visibleJobKeys,
  ]);

  return <RunTimeline loading={loading} range={range} jobs={visibleJobs} />;
};
