import {useMutation} from '@apollo/client';
import {useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {LAUNCH_PIPELINE_REEXECUTION_MUTATION, handleLaunchResult} from './RunUtils';
import {
  LaunchPipelineReexecutionMutation,
  LaunchPipelineReexecutionMutationVariables,
} from './types/RunUtils.types';
import {ExecutionParams, ReexecutionStrategy} from '../graphql/types';
import {showLaunchError} from '../launchpad/showLaunchError';

/**
 * This hook gives you a mutation method that you can use to re-execute runs.
 *
 * The preferred way to re-execute runs is to pass a ReexecutionStrategy.
 * If you need to re-execute with more complex parameters, (eg: a custom subset
 * of the previous run), build the variables using `getReexecutionVariables` and
 * pass them to this hook.
 */
export const useJobReexecution = (opts?: {onCompleted?: () => void}) => {
  const history = useHistory();
  const {onCompleted} = opts || {};

  const [launchPipelineReexecution] = useMutation<
    LaunchPipelineReexecutionMutation,
    LaunchPipelineReexecutionMutationVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);

  return useCallback(
    async (
      run: {id: string; pipelineName: string},
      param: ReexecutionStrategy | ExecutionParams,
    ) => {
      try {
        const result = await launchPipelineReexecution({
          variables:
            typeof param === 'string'
              ? {reexecutionParams: {parentRunId: run.id, strategy: param}}
              : {executionParams: param},
        });
        handleLaunchResult(run.pipelineName, result.data?.launchPipelineReexecution, history, {
          preserveQuerystring: true,
          behavior: 'open',
        });
        onCompleted?.();
      } catch (error) {
        showLaunchError(error as Error);
      }
    },
    [history, launchPipelineReexecution, onCompleted],
  );
};
