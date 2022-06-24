import {useMutation} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router';

import {showLaunchError} from '../launchpad/showLaunchError';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';

import {
  getReexecutionVariables,
  handleLaunchResult,
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  ReExecutionStyle,
} from './RunUtils';
import {
  LaunchPipelineReexecution,
  LaunchPipelineReexecutionVariables,
} from './types/LaunchPipelineReexecution';
import {RunFragment} from './types/RunFragment';

export const useJobReExecution = (run: RunFragment | undefined | null) => {
  const history = useHistory();
  const [launchPipelineReexecution] = useMutation<
    LaunchPipelineReexecution,
    LaunchPipelineReexecutionVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const repoMatch = useRepositoryForRun(run);

  return React.useCallback(
    async (style: ReExecutionStyle) => {
      if (!run || !run.pipelineSnapshotId || !repoMatch) {
        return;
      }

      const variables = getReexecutionVariables({
        run,
        runConfigYaml: run.runConfig.yaml,
        style,
        repositoryLocationName: repoMatch.match.repositoryLocation.name,
        repositoryName: repoMatch.match.repository.name,
      });

      try {
        const result = await launchPipelineReexecution({variables});
        handleLaunchResult(run.pipelineName, result, history, {
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
