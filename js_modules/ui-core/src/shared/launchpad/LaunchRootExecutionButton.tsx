import {useLaunchWithTelemetry} from '@shared/launchpad/useLaunchWithTelemetry';
import * as React from 'react';

import {IconName} from '../../../../ui-components/src';
import {LaunchButton} from '../../launchpad/LaunchButton';
import {LaunchBehavior} from '../../runs/RunUtils';
import {LaunchPipelineExecutionMutationVariables} from '../../runs/types/RunUtils.types';

interface LaunchRootExecutionButtonProps {
  disabled: boolean;
  hasLaunchPermission: boolean;
  warning?: React.ReactNode;
  getVariables: () => undefined | LaunchPipelineExecutionMutationVariables;
  behavior: LaunchBehavior;
  pipelineName: string;
  title?: string;
  icon?: IconName;
}

export const NO_LAUNCH_PERMISSION_MESSAGE = 'You do not have permission to launch this job';

export const LaunchRootExecutionButton = (props: LaunchRootExecutionButtonProps) => {
  const {hasLaunchPermission} = props;
  const launchWithTelemetry = useLaunchWithTelemetry();

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
        disabled: props.disabled || !hasLaunchPermission,
        tooltip: !hasLaunchPermission ? NO_LAUNCH_PERMISSION_MESSAGE : undefined,
      }}
    />
  );
};
