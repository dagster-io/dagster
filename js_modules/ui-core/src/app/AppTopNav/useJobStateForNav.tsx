import {useMemo} from 'react';

import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {useRepositoryOptions} from '../../workspace/WorkspaceContext/util';

export type JobStateForNav = 'unknown' | 'has-jobs' | 'no-jobs';

/**
 * Determine whether the viewer has any jobs in any of their code locations. We use
 * this information to determine whether to show the "Jobs" item in the top navigation
 * at all. If there are no jobs, we won't show it.
 */
export const useJobStateForNav = () => {
  const {options, loading} = useRepositoryOptions();
  return useMemo(() => {
    if (loading) {
      return 'unknown';
    }

    const hasJobs = options.some((option) =>
      option.repository.pipelines.some((job) => !isHiddenAssetGroupJob(job.name)),
    );

    return hasJobs ? 'has-jobs' : 'no-jobs';
  }, [options, loading]);
};
