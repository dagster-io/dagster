import {useMutation} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router';

import {IconName} from '../../../ui/src';
import {usePermissions} from '../app/Permissions';
import {TelemetryAction, useTelemetryAction} from '../app/Telemetry';
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  handleLaunchResult,
  LaunchBehavior,
} from '../runs/RunUtils';
import {
  LaunchPipelineExecution,
  LaunchPipelineExecutionVariables,
} from '../runs/types/LaunchPipelineExecution';

import {LaunchButton} from './LaunchButton';
import {showLaunchError} from './showLaunchError';

interface LaunchRootExecutionButtonProps {
  disabled: boolean;
  getVariables: () => undefined | LaunchPipelineExecutionVariables;
  behavior: LaunchBehavior;
  pipelineName: string;
  title?: string;
  icon?: IconName;
}

export function useLaunchWithTelemetry() {
  const {canLaunchPipelineExecution} = usePermissions();
  const [launchPipelineExecution] = useMutation<
    LaunchPipelineExecution,
    LaunchPipelineExecutionVariables
  >(LAUNCH_PIPELINE_EXECUTION_MUTATION);
  const logTelemetry = useTelemetryAction();
  const history = useHistory();

  return React.useCallback(
    async (variables: LaunchPipelineExecutionVariables, behavior: LaunchBehavior) => {
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
        handleLaunchResult(jobName, result, history, {behavior});
      } catch (error) {
        showLaunchError(error as Error);
      }

      return result.data;
    },
    [canLaunchPipelineExecution, history, launchPipelineExecution, logTelemetry],
  );
}

export const LaunchRootExecutionButton: React.FC<LaunchRootExecutionButtonProps> = (props) => {
  const launchWithTelemetry = useLaunchWithTelemetry();
  const {canLaunchPipelineExecution} = usePermissions();

  const onLaunch = async () => {
    const variables = props.getVariables();
    if (variables == null) {
      return;
    }
    await launchWithTelemetry(variables, props.behavior);
  };

  return (
    <LaunchButton
      runCount={1}
      config={{
        onClick: onLaunch,
        icon: props.icon || 'open_in_new',
        title: props.title || 'Launch Run',
        disabled: props.disabled || !canLaunchPipelineExecution.enabled,
        tooltip: !canLaunchPipelineExecution.enabled
          ? canLaunchPipelineExecution.disabledReason
          : undefined,
      }}
    />
  );
};
