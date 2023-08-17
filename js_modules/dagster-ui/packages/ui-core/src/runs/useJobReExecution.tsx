import {useMutation} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router';

import {showLaunchError} from '../launchpad/showLaunchError';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';

import {
  getReexecutionVariables,
  handleLaunchResult,
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  ReExecutionStyle,
} from './RunUtils';
import {RunPageFragment} from './types/RunFragments.types';
import {
  LaunchPipelineReexecutionMutation,
  LaunchPipelineReexecutionMutationVariables,
} from './types/RunUtils.types';

export const useJobReExecution = (run: RunPageFragment | undefined | null) => {
  const history = useHistory();
  const [launchPipelineReexecution] = useMutation<
    LaunchPipelineReexecutionMutation,
    LaunchPipelineReexecutionMutationVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);

  const repoMatch = useRepositoryForRunWithParentSnapshot(run);

  return React.useCallback(
    async (style: ReExecutionStyle) => {
      if (!run || !run.pipelineSnapshotId || !repoMatch) {
        return;
      }

      const variables = getReexecutionVariables({
        run,
        style,
        repositoryLocationName: repoMatch.match.repositoryLocation.name,
        repositoryName: repoMatch.match.repository.name,
      });

      try {
        const result = await launchPipelineReexecution({variables});
        handleLaunchResult(run.pipelineName, result.data?.launchPipelineReexecution, history, {
          preserveQuerystring: true,
          behavior: 'open',
        });
      } catch (error) {
        showLaunchError(error as Error);
      }
    },
    [history, launchPipelineReexecution, repoMatch, run],
  );
};
