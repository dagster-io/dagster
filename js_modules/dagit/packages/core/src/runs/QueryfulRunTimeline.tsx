import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {RunsFilter} from '../types/globalTypes';
import {LoadingSpinner} from '../ui/Loading';

import {RunTimeline} from './RunTimeline';
import {useRunsForTimeline} from './useRunsForTimeline';

interface Props {
  range: [number, number];
  runsFilter?: RunsFilter;
  visibleJobKeys: Set<string>;
}

export const QueryfulRunTimeline = (props: Props) => {
  const {range, visibleJobKeys, runsFilter = {}} = props;
  const {flagRunBucketing} = useFeatureFlags();
  const {jobs, loading} = useRunsForTimeline(range, runsFilter);

  const visibleJobs = React.useMemo(() => jobs.filter(({key}) => visibleJobKeys.has(key)), [
    jobs,
    visibleJobKeys,
  ]);

  if (loading) {
    return <LoadingSpinner purpose="section" />;
  }

  return <RunTimeline range={range} jobs={visibleJobs} bucketByRepo={flagRunBucketing} />;
};
