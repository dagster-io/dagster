import * as React from 'react';
import {useMutation} from 'react-apollo';

import {LaunchButton} from 'src/execute/LaunchButton';
import {LAUNCH_PIPELINE_EXECUTION_MUTATION, handleLaunchResult} from 'src/runs/RunUtils';
import {LaunchPipelineExecutionVariables} from 'src/runs/types/LaunchPipelineExecution';

interface LaunchRootExecutionButtonProps {
  disabled: boolean;
  getVariables: () => undefined | LaunchPipelineExecutionVariables;
  pipelineName: string;
}

export const LaunchRootExecutionButton: React.FunctionComponent<LaunchRootExecutionButtonProps> = (
  props,
) => {
  const [launchPipelineExecution] = useMutation(LAUNCH_PIPELINE_EXECUTION_MUTATION);

  const onLaunch = async () => {
    const variables = props.getVariables();
    if (variables == null) {
      return;
    }

    try {
      const result = await launchPipelineExecution({variables});
      handleLaunchResult(props.pipelineName, result, {
        openInNewWindow: true,
      });
    } catch (error) {
      console.error('Error launching run:', error);
    }
  };

  return (
    <div style={{marginRight: 20}}>
      <LaunchButton
        config={{
          icon: 'send-to',
          onClick: onLaunch,
          title: 'Launch Execution',
          disabled: props.disabled,
        }}
      />
    </div>
  );
};
