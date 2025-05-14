import {useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {showLaunchError} from './showLaunchError';
import {useMutation} from '../apollo-client';
import {paramsWithUIExecutionTags} from './uiExecutionTags';
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
    async (
      {executionParams, ...rest}: LaunchPipelineExecutionMutationVariables,
      behavior: LaunchBehavior,
    ) => {
      const jobName = executionParams.selector.jobName || executionParams.selector.pipelineName;

      if (!jobName) {
        return;
      }

      const metadata: {[key: string]: string | null | undefined} = {
        jobName,
        opSelection: executionParams.selector.solidSelection ? 'provided' : undefined,
      };

      const finalized = {executionParams: paramsWithUIExecutionTags(executionParams), ...rest};
      const result = await launchPipelineExecution({variables: finalized});
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
