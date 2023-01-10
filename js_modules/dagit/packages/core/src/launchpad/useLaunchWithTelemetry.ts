import {useMutation} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router';

import {usePermissionsDEPRECATED} from '../app/Permissions';
import {TelemetryAction, useTelemetryAction} from '../app/Telemetry';
import {LaunchPipelineExecutionMutationVariables} from '../graphql/graphql';
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  handleLaunchResult,
  LaunchBehavior,
} from '../runs/RunUtils';

import {showLaunchError} from './showLaunchError';

export function useLaunchWithTelemetry() {
  const {canLaunchPipelineExecution} = usePermissionsDEPRECATED();
  const [launchPipelineExecution] = useMutation(LAUNCH_PIPELINE_EXECUTION_MUTATION);
  const logTelemetry = useTelemetryAction();
  const history = useHistory();

  return React.useCallback(
    async (variables: LaunchPipelineExecutionMutationVariables, behavior: LaunchBehavior) => {
      const jobName =
        variables.executionParams.selector.jobName ||
        variables.executionParams.selector.pipelineName;

      if (!canLaunchPipelineExecution.enabled || !jobName) {
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
    [canLaunchPipelineExecution, history, launchPipelineExecution, logTelemetry],
  );
}
