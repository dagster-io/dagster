import {useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {showLaunchError} from './showLaunchError';
import {useMutation} from '../apollo-client';
import {TelemetryAction, useTelemetryAction} from '../app/Telemetry';
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  LaunchBehavior,
  handleLaunchResult,
} from '../runs/RunUtils';
import {
  LaunchPipelineExecutionMutation,
  LaunchPipelineExecutionMutationVariables,
} from '../runs/types/RunUtils.types';

export function useLaunchWithTelemetry() {
  const [launchPipelineExecution] = useMutation<
    LaunchPipelineExecutionMutation,
    LaunchPipelineExecutionMutationVariables
  >(LAUNCH_PIPELINE_EXECUTION_MUTATION, {
    refetchQueries: ['AssetChecksQuery', 'AssetCheckDetailsQuery'],
  });
  const logTelemetry = useTelemetryAction();
  const history = useHistory();

  return useCallback(
    async (variables: LaunchPipelineExecutionMutationVariables, behavior: LaunchBehavior) => {
      const jobName =
        variables.executionParams.selector.jobName ||
        variables.executionParams.selector.pipelineName;

      if (!jobName) {
        return;
      }

      const metadata: {[key: string]: string | null | undefined} = {
        jobName,
        opSelection: variables.executionParams.selector.solidSelection ? 'provided' : undefined,
      };

      const result = await launchPipelineExecution({variables});
      logTelemetry(TelemetryAction.LAUNCH_RUN, metadata);
      try {
        handleLaunchResult(jobName, result.data?.launchPipelineExecution, history, {behavior});
      } catch (error) {
        showLaunchError(error as Error);
      }

      return result.data?.launchPipelineExecution;
    },
    [history, launchPipelineExecution, logTelemetry],
  );
}
