import * as React from "react";
import styled from "styled-components/macro";
import { IconNames } from "@blueprintjs/icons";
import {
  Menu,
  MenuItem,
  Popover,
  PopoverInteractionKind,
  Button,
  Intent,
  Tooltip,
  Position
} from "@blueprintjs/core";
import { useMutation } from "react-apollo";
import ExecutionStartButton from "../execute/ExecutionStartButton";
import { PipelineRunStatus } from "../types/globalTypes";
import { ExecutionType } from "../LocalStorage";

import { CANCEL_MUTATION } from "./RunUtils";
import { SharedToaster } from "../DomUtils";
import { IStepState } from "../RunMetadataProvider";

const CANCEL_TITLE = "Terminate";

// Title of re-execute button group
const LAUNCH_REEXECUTE_TITLE = "Launch Re-execution";

// Titles of re-execute options
const REEXECUTE_FULL_PIPELINE_TITLE = "Full Pipeline";
const REEXECUTE_SUBSET_NO_SELECTION_TITLE = "Step Not Selected";
const REEXECUTE_SUBSET_TITLE = `Selected Step Subset`;
const REEXECUTE_FROM_FAILURE_TITLE = "From Failure";

// Descriptions of re-execute options
export const REEXECUTE_PIPELINE_UNKNOWN =
  "Re-execute is unavailable because the pipeline is not present in the current repository.";

const REEXECUTE_FULL_PIPELINE_DESCRIPTION =
  "Re-execute the pipeline run from scratch";

const REEXECUTE_SUBSET =
  "Re-run the following steps with existing configuration:";
const REEXECUTE_SUBSET_NO_SELECTION =
  "Re-execute is only enabled when steps are selected. Try selecting a step or typing a step subset to re-execute.";
const REEXECUTE_SUBSET_NO_ARTIFACTS =
  "Use a persisting storage mode such as 'filesystem' to enable step re-execution";
const REEXECUTE_SUBSET_NOT_DONE =
  "Wait for the selected steps to finish to re-execute it.";

const RETRY_DESCRIPTION =
  "Retry the pipeline run, skipping steps that completed successfully";
const RETRY_DISABLED = "Retry is only enabled when the pipeline has failed.";
const RETRY_NO_ARTIFACTS =
  "Retry is only enabled on persistent storage. Try rerunning with a different storage configuration.";

interface RunActionButtonsRun {
  runId: string;
  status: PipelineRunStatus;
  pipeline: {
    __typename: string;
  };
  canTerminate: boolean;
}

interface RunActionButtonsProps {
  run?: RunActionButtonsRun;
  selectedSteps: string[];
  selectedStepStates: IStepState[];
  artifactsPersisted: boolean;
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
  onLaunch: (stepKeys?: string[], resumeRetry?: boolean) => Promise<void>;
}

const CancelRunButton: React.FunctionComponent<{
  run: RunActionButtonsRun;
}> = ({ run }) => {
  const [cancel] = useMutation(CANCEL_MUTATION);
  const [inFlight, setInFlight] = React.useState(false);
  return (
    <Button
      icon={IconNames.STOP}
      small={true}
      text={CANCEL_TITLE}
      intent="warning"
      disabled={inFlight}
      onClick={async () => {
        setInFlight(true);
        const res = await cancel({
          variables: { runId: run.runId }
        });
        setInFlight(false);
        if (res.data?.terminatePipelineExecution?.message) {
          SharedToaster.show({
            message: res.data.terminatePipelineExecution.message,
            icon: "error",
            intent: Intent.DANGER
          });
        }
      }}
    />
  );
};

interface ReexecuteButtonProps {
  selectedSteps?: string[];
  artifactsPersisted?: boolean;
  onChangeExecutionType?: (type: ExecutionType) => void;
  onClick: (stepKeys?: string[], resumeRetry?: boolean) => void;
  disabled?: boolean;
  stepsInFlight?: boolean;
}

export function ReexecuteFullPipelineButton(props: ReexecuteButtonProps) {
  const { onClick } = props;

  return (
    <Tooltip
      hoverOpenDelay={300}
      position={Position.LEFT}
      openOnTargetFocus={false}
      targetTagName="div"
      content={REEXECUTE_FULL_PIPELINE_DESCRIPTION}
    >
      <ReexecuteMenuItem
        text={REEXECUTE_FULL_PIPELINE_TITLE}
        icon="repeat"
        onClick={() => onClick()}
      />
    </Tooltip>
  );
}

export function ReexecuteSubsetButton(props: ReexecuteButtonProps) {
  const { onClick, selectedSteps, stepsInFlight, artifactsPersisted } = props;

  const disabled =
    !selectedSteps ||
    selectedSteps.length === 0 ||
    stepsInFlight ||
    !artifactsPersisted;

  return (
    <Tooltip
      hoverOpenDelay={300}
      position={Position.LEFT}
      targetTagName="div"
      openOnTargetFocus={false}
      interactionKind={PopoverInteractionKind.HOVER}
      content={
        <div>
          {!artifactsPersisted
            ? REEXECUTE_SUBSET_NO_ARTIFACTS
            : !selectedSteps || selectedSteps.length === 0
            ? REEXECUTE_SUBSET_NO_SELECTION
            : stepsInFlight
            ? REEXECUTE_SUBSET_NOT_DONE
            : REEXECUTE_SUBSET}
          <div style={{ paddingLeft: "10px" }}>
            {selectedSteps &&
              selectedSteps.length > 0 &&
              selectedSteps.map(step => (
                <span
                  key={step}
                  style={{ display: "block" }}
                >{`* ${step}`}</span>
              ))}
          </div>
        </div>
      }
    >
      <ReexecuteMenuItem
        text={
          selectedSteps && selectedSteps.length > 0
            ? REEXECUTE_SUBSET_TITLE
            : REEXECUTE_SUBSET_NO_SELECTION_TITLE
        }
        icon="select"
        disabled={disabled}
        onClick={() => onClick(selectedSteps)}
      />
    </Tooltip>
  );
}

export function ReexecuteFromFailureButton(props: ReexecuteButtonProps) {
  const { onClick, disabled, artifactsPersisted } = props;
  return (
    <Tooltip
      hoverOpenDelay={300}
      content={
        !artifactsPersisted
          ? RETRY_NO_ARTIFACTS
          : disabled
          ? RETRY_DISABLED
          : RETRY_DESCRIPTION
      }
      position={Position.LEFT}
      targetTagName="div"
      openOnTargetFocus={false}
    >
      <ReexecuteMenuItem
        text={REEXECUTE_FROM_FAILURE_TITLE}
        disabled={disabled || !artifactsPersisted}
        onClick={() => onClick(undefined, true)}
        icon="play"
      />
    </Tooltip>
  );
}

interface ReexecuteButtonGroupProps {
  selectedSteps: string[];
  artifactsPersisted: boolean;
  onClick: (stepKeys?: string[], resumeRetry?: boolean) => void;
  isPipelineUnknown: boolean;
  run?: RunActionButtonsRun;
  selectedStepStates: IStepState[];
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
}

export function ReexecuteButtonGroup(props: ReexecuteButtonGroupProps) {
  const {
    selectedSteps,
    artifactsPersisted,
    onClick,
    isPipelineUnknown,
    run,
    selectedStepStates,
    executionPlan
  } = props;
  // Run's status
  const isRetryDisabled = !(
    executionPlan &&
    run &&
    run.status === PipelineRunStatus.FAILURE
  );
  const stepsInFlight = selectedStepStates
    .map(
      stepState =>
        ![IStepState.FAILED, IStepState.SUCCEEDED].includes(stepState)
    )
    .every(Boolean);

  return (
    <Popover
      content={
        <Menu>
          <ReexecuteFullPipelineButton onClick={onClick} />
          <ReexecuteSubsetButton
            onClick={onClick}
            selectedSteps={selectedSteps}
            stepsInFlight={stepsInFlight}
            artifactsPersisted={artifactsPersisted}
          />
          <ReexecuteFromFailureButton
            onClick={onClick}
            disabled={isRetryDisabled}
            artifactsPersisted={artifactsPersisted}
          />
        </Menu>
      }
      position={"bottom"}
      // Disable the whole button group if pipeline is unknown
      disabled={isPipelineUnknown}
    >
      <Tooltip
        content={REEXECUTE_PIPELINE_UNKNOWN}
        position={Position.BOTTOM}
        disabled={!isPipelineUnknown}
      >
        <Button
          small={true}
          text={LAUNCH_REEXECUTE_TITLE}
          icon="repeat"
          rightIcon="caret-down"
          disabled={isPipelineUnknown}
          intent={isPipelineUnknown ? "none" : "primary"}
        />
      </Tooltip>
    </Popover>
  );
}

export const RunActionButtons: React.FunctionComponent<RunActionButtonsProps> = props => {
  const [starting, setStarting] = React.useState(false);
  const { run, executionPlan, onLaunch } = props;
  const isPipelineUnknown = run?.pipeline.__typename === "UnknownPipeline";
  const isReexecutionDisabled = !(
    run?.status === PipelineRunStatus.FAILURE ||
    run?.status === PipelineRunStatus.SUCCESS
  );

  return (
    <>
      <ExecutionStartButton
        title={LAUNCH_REEXECUTE_TITLE}
        icon="repeat"
        onClick={() => {}}
        starting={starting}
        disabled={isReexecutionDisabled}
        small={true}
      >
        <ReexecuteButtonGroup
          // Launch re-execution button group
          onClick={async (...args) => {
            setStarting(true);
            await onLaunch(...args);
            setStarting(false);
          }}
          selectedSteps={props.selectedSteps}
          artifactsPersisted={props.artifactsPersisted}
          isPipelineUnknown={isPipelineUnknown}
          run={run}
          selectedStepStates={props.selectedStepStates}
          executionPlan={executionPlan}
        />
      </ExecutionStartButton>
      {run?.canTerminate && (
        <>
          <div style={{ minWidth: 6 }} />
          <CancelRunButton run={run} />
        </>
      )}
    </>
  );
};

const ReexecuteMenuItem = styled(MenuItem)`
  max-width: 200px;
`;
