import * as React from 'react';

import {IconName} from '../../../ui/src';
import {usePermissionsDEPRECATED} from '../app/Permissions';
import {LaunchPipelineExecutionMutationVariables} from '../graphql/graphql';
import {LaunchBehavior} from '../runs/RunUtils';

import {LaunchButton} from './LaunchButton';
import {useLaunchPadHooks} from './LaunchpadHooksContext';

interface LaunchRootExecutionButtonProps {
  disabled: boolean;
  warning?: React.ReactNode;
  getVariables: () => undefined | LaunchPipelineExecutionMutationVariables;
  behavior: LaunchBehavior;
  pipelineName: string;
  title?: string;
  icon?: IconName;
}

export const LaunchRootExecutionButton: React.FC<LaunchRootExecutionButtonProps> = (props) => {
  const {useLaunchWithTelemetry} = useLaunchPadHooks();
  const launchWithTelemetry = useLaunchWithTelemetry();
  const {canLaunchPipelineExecution} = usePermissionsDEPRECATED();

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
        warning: props.warning || undefined,
        disabled: props.disabled || !canLaunchPipelineExecution.enabled,
        tooltip: !canLaunchPipelineExecution.enabled
          ? canLaunchPipelineExecution.disabledReason
          : undefined,
      }}
    />
  );
};
