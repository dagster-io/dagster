import * as React from "react";
import gql from "graphql-tag";
import {
  Icon,
  ButtonGroup,
  Popover,
  Position,
  Menu,
  MenuItem
} from "@blueprintjs/core";
import { IconNames, IconName } from "@blueprintjs/icons";
import { useMutation, useQuery } from "react-apollo";
import { useStorage, ExecutionType } from "../LocalStorage";

import ExecutionStartButton, { ExecutionButton } from "./ExecutionStartButton";
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
  const [localData, onSaveLocal] = useStorage();

  const startButton = (
    <ExecutionStartButton
      title="Start Execution"
      icon={IconNames.PLAY}
      tooltip="Start execution in a subprocess"
      activeText="Starting..."
      shortcutLabel={`⌥G`}
      shortcutFilter={e => e.keyCode === 71 && e.altKey}
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
  );

  if (!data?.instance?.runLauncher?.name) {
    return startButton;
  }

  const launchButton = (
    <ExecutionStartButton
      title="Launch Execution"
      icon={IconNames.SEND_TO}
      tooltip={`Launch execution via ${data.instance.runLauncher.name}`}
      activeText="Launching..."
      shortcutLabel={`⌥L`}
      shortcutFilter={e => e.keyCode === 76 && e.altKey}
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
  );

  const selectedButton =
    localData.selectedExecutionType === ExecutionType.LAUNCH
      ? launchButton
      : startButton;

  const onSelectExecutionType = (selectedExecutionType: ExecutionType) => {
    onSaveLocal({ ...localData, selectedExecutionType });
  };

  return (
    <>
      <ButtonGroup>
        {selectedButton}
        <Popover
          position={Position.BOTTOM_RIGHT}
          modifiers={{ arrow: { enabled: false } }}
        >
          <ExecutionButton>
            <Icon icon={IconNames.CARET_DOWN} iconSize={17} />
          </ExecutionButton>
          <Menu style={{ padding: 0 }} large={true}>
            <ExecutionMenuItem
              title="Start Execution"
              description="Start pipeline execution in a spawned subprocess"
              icon={IconNames.PLAY}
              onSelect={onSelectExecutionType}
              type={ExecutionType.START}
            />
            <ExecutionMenuItem
              title="Launch Execution"
              description={`Launch / enqueue execution via ${data.instance.runLauncher.name}`}
              icon={IconNames.SEND_TO}
              onSelect={onSelectExecutionType}
              type={ExecutionType.LAUNCH}
            />
          </Menu>
        </Popover>
      </ButtonGroup>
    </>
  );
};

interface IExecutionMenuItem {
  title: string;
  description: React.ReactNode;
  type: ExecutionType;
  icon: IconName;
  onSelect: (type: ExecutionType) => void;
}

const ExecutionMenuItem = ({
  title,
  description,
  type,
  icon,
  onSelect
}: IExecutionMenuItem) => {
  return (
    <MenuItem
      text={
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center"
          }}
        >
          <Icon
            icon={icon}
            iconSize={17}
            style={{ marginRight: 15, marginBottom: 5 }}
          />
          <div>
            {title}
            <div style={{ fontSize: 12, color: "#666" }}>{description}</div>
          </div>
        </div>
      }
      style={{ padding: "10px 20px", minWidth: 200 }}
      onClick={() => {
        onSelect(type);
      }}
    />
  );
};
