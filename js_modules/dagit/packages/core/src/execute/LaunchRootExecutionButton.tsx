import {useMutation} from '@apollo/client';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {LAUNCH_PIPELINE_EXECUTION_MUTATION, handleLaunchResult} from '../runs/RunUtils';
import {
  LaunchPipelineExecution,
  LaunchPipelineExecutionVariables,
} from '../runs/types/LaunchPipelineExecution';

import {LaunchButton} from './LaunchButton';
import {showLaunchError} from './showLaunchError';

interface LaunchRootExecutionButtonProps {
  disabled: boolean;
  getVariables: () => undefined | LaunchPipelineExecutionVariables;
  pipelineName: string;
}

export const LaunchRootExecutionButton: React.FunctionComponent<LaunchRootExecutionButtonProps> = (
  props,
) => {
  const {canLaunchPipelineExecution} = usePermissions();
  const [launchPipelineExecution] = useMutation<LaunchPipelineExecution>(
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
  );
  const {basePath} = React.useContext(AppContext);

  const onLaunch = async () => {
    const variables = props.getVariables();
    if (variables == null) {
      return;
    }

    try {
      const result = await launchPipelineExecution({variables});
      handleLaunchResult(basePath, props.pipelineName, result);
    } catch (error) {
      showLaunchError(error as Error);
    }
  };

  return (
    <div style={{marginRight: 20}}>
      <LaunchButton
        runCount={1}
        config={{
          icon: 'send-to',
          onClick: onLaunch,
          title: 'Launch Execution',
          disabled: props.disabled || !canLaunchPipelineExecution,
          tooltip: !canLaunchPipelineExecution ? DISABLED_MESSAGE : undefined,
        }}
      />
    </div>
  );
};
