import * as React from "react";
import gql from "graphql-tag";
import {
  Icon,
  IconName,
  ButtonGroup,
  Popover,
  Position,
  Menu,
  MenuItem
} from "@blueprintjs/core";
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
import { IconNames } from "@blueprintjs/icons";

const RUN_LAUNCHER_QUERY = gql`
  query RunLauncher {
    instance {
      runLauncher {
        name
      }
      disableRunStart
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

  const onExecute = async () => {
    const variables = props.getVariables();
    if (!variables) {
      return;
    }

    const result = await startPipelineExecution({ variables });
    handleExecutionResult(props.pipelineName, result, {
      openInNewWindow: true
    });
  };

  const onLaunch = async () => {
    const variables = props.getVariables();
    if (variables == null) {
      return;
    }

    const result = await launchPipelineExecution({ variables });
    handleExecutionResult(props.pipelineName, result, {
      openInNewWindow: true
    });
  };

  return (
    <LaunchButtonGroup>
      <ExecutionStartButton
        title="Start Execution"
        icon={IconNames.PLAY}
        tooltip="Start execution in a subprocess"
        activeText="Starting..."
        shortcutLabel={`⌥G`}
        shortcutFilter={e => e.keyCode === 71 && e.altKey}
        onClick={onExecute}
      />
      <ExecutionStartButton
        title="Launch Execution"
        icon={IconNames.SEND_TO}
        tooltip="Launch execution"
        activeText="Launching..."
        shortcutLabel={`⌥L`}
        shortcutFilter={e => e.keyCode === 76 && e.altKey}
        onClick={onLaunch}
      />
    </LaunchButtonGroup>
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

export const LaunchButtonGroup = ({
  children,
  small,
  onChange
}: {
  children: React.ReactNode;
  small?: boolean;
  onChange?: (type: ExecutionType) => void;
}) => {
  const [localData, onSaveLocal] = useStorage();
  const { data } = useQuery(RUN_LAUNCHER_QUERY);

  if (!children) {
    return;
  }

  const startButton = children[0];
  const launchButton = children[1];

  if (!data?.instance?.runLauncher?.name) {
    return startButton;
  }

  if (data?.instance?.disableRunStart) {
    return launchButton;
  }

  const selectedButton =
    localData.selectedExecutionType === ExecutionType.LAUNCH
      ? launchButton
      : startButton;

  const onSelectExecutionType = (selectedExecutionType: ExecutionType) => {
    onSaveLocal({ ...localData, selectedExecutionType });
    onChange && onChange(selectedExecutionType);
  };

  return (
    <>
      <ButtonGroup>
        {selectedButton}
        <Popover
          position={Position.BOTTOM_RIGHT}
          modifiers={{ arrow: { enabled: false } }}
        >
          <ExecutionButton small={small}>
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
