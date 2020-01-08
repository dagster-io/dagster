import * as React from "react";
import gql from "graphql-tag";
import { IconNames } from "@blueprintjs/icons";
import { useMutation, useQuery } from "react-apollo";

import ExecutionStartButton from "./ExecutionStartButton";
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  START_PIPELINE_EXECUTION_MUTATION,
  handleExecutionResult
} from "../runs/RunUtils";
import { StartPipelineExecutionVariables } from "../runs/types/StartPipelineExecution";
import { LaunchPipelineExecutionVariables } from "../runs/types/LaunchPipelineExecution";

const RUN_LAUNCHER_QUERY = gql`
  query RunLauncher {
    instance {
      runLauncher {
        name
      }
    }
  }
`;

export const PipelineExecutionButtonGroup = (props: {
  getVariables: () =>
    | undefined
    | StartPipelineExecutionVariables
    | LaunchPipelineExecutionVariables;
  pipelineName: string;
}) => {
  const [startPipelineExecution] = useMutation(
    START_PIPELINE_EXECUTION_MUTATION
  );
  const [launchPipelineExecution] = useMutation(
    LAUNCH_PIPELINE_EXECUTION_MUTATION
  );
  const { data } = useQuery(RUN_LAUNCHER_QUERY);

  return (
    <>
      <ExecutionStartButton
        title="Start Execution"
        icon={IconNames.PLAY}
        tooltip="Start execution in a subprocess"
        activeText="Starting..."
        onClick={async () => {
          const variables = props.getVariables();
          if (!variables) {
            return;
          }

          const result = await startPipelineExecution({ variables });
          handleExecutionResult(props.pipelineName, result, {
            openInNewWindow: true
          });
        }}
      />
      {data?.instance?.runLauncher?.name ? (
        <ExecutionStartButton
          title="Launch Execution"
          icon={IconNames.SEND_TO}
          tooltip={`Launch execution via ${data.instance.runLauncher.name}`}
          activeText="Launching..."
          onClick={async () => {
            const variables = props.getVariables();
            if (variables == null) {
              return;
            }

            const result = await launchPipelineExecution({ variables });
            handleExecutionResult(props.pipelineName, result, {
              openInNewWindow: true
            });
          }}
        />
      ) : null}
    </>
  );
};
