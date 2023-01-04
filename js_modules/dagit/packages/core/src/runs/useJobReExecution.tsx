import {useMutation} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router';

import {RunFragmentFragment} from '../graphql/graphql';
import {showLaunchError} from '../launchpad/showLaunchError';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';

import {
  getReexecutionVariables,
  handleLaunchResult,
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  ReExecutionStyle,
} from './RunUtils';

export const useJobReExecution = (run: RunFragmentFragment | undefined | null) => {
  const history = useHistory();
  const [launchPipelineReexecution] = useMutation(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const repoMatch = useRepositoryForRun(run);

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
