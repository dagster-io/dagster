import {useLaunchWithTelemetry} from '@shared/launchpad/useLaunchWithTelemetry';
import * as React from 'react';

import {IconName} from '../../../../ui-components/src';
import {isNewTabClick} from '../../hooks/useOpenInNewTab';
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

  const onLaunch = async (e: React.MouseEvent | KeyboardEvent) => {
    const variables = props.getVariables();
    if (variables == null) {
      return;
    }
    const openInNewTab = isNewTabClick(e);
    await launchWithTelemetry(variables, {behavior: props.behavior, openInNewTab});
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
