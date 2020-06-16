import * as React from "react";
import { useMutation } from "react-apollo";

import ExecutionStartButton from "./ExecutionStartButton";
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  handleExecutionResult
} from "../runs/RunUtils";
import { LaunchPipelineExecutionVariables } from "../runs/types/LaunchPipelineExecution";
import { IconNames } from "@blueprintjs/icons";

interface PipelineExecutionButtonGroupProps {
  disabled?: boolean;
  getVariables: () => undefined | LaunchPipelineExecutionVariables;
  pipelineName: string;
}

export const PipelineExecutionButtonGroup: React.FunctionComponent<PipelineExecutionButtonGroupProps> = props => {
  const [launchPipelineExecution] = useMutation(
    LAUNCH_PIPELINE_EXECUTION_MUTATION
  );

  const onLaunch = async () => {
    const variables = props.getVariables();
    if (variables == null) {
      return;
    }

    try {
      const result = await launchPipelineExecution({ variables });
      handleExecutionResult(props.pipelineName, result, {
        openInNewWindow: true
      });
    } catch (error) {
      console.error("Error launching run:", error);
    }
  };

  return (
    <div style={{ marginRight: 20 }}>
      <ExecutionStartButton
        title="Launch Execution"
        icon={IconNames.SEND_TO}
        tooltip="Launch execution"
        activeText="Launching..."
        shortcutLabel={`⌥L`}
        shortcutFilter={e => e.keyCode === 76 && e.altKey}
        onClick={onLaunch}
        disabled={props.disabled}
      />
    </div>
  );
};
