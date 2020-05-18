import * as React from "react";
import styled from "styled-components/macro";
import { IconNames } from "@blueprintjs/icons";
import {
  Menu,
  MenuItem,
  Popover,
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
import { LaunchButtonGroup } from "../execute/PipelineExecutionButtonGroup";

const CANCEL_TITLE = "Terminate";

// Title of re-execute button group
const START_REEXECUTE_TITLE = "Re-execute";
const LAUNCH_REEXECUTE_TITLE = "Launch Re-execution";

// Titles of re-execute options
const REEXECUTE_FULL_PIPELINE_TITLE = "Full Pipeline";
const REEXECUTE_SUBSET_DEFAULT_TITLE = "Step Not Selected";
const REEXECUTE_FROM_FAILURE_TITLE = "From Failure";

// Descriptions of re-execute options
export const REEXECUTE_PIPELINE_UNKNOWN =
  "Re-execute is unavailable because the pipeline is not present in the current repository.";

const REEXECUTE_FULL_PIPELINE_DESCRIPTION =
  "Re-execute the pipeline run from scratch";

const REEXECUTE_SINGLE_STEP =
  "Re-run just this step with existing configuration.";
const REEXECUTE_SINGLE_STEP_NO_SELECTION =
  "Re-execute is only enabled when a step is selected. Try selecting a step to re-execute.";
const REEXECUTE_SINGLE_STEP_NO_ARTIFACTS =
  "Use a persisting storage mode such as 'filesystem' to enable single step re-execution";
const REEXECUTE_SINGLE_STEP_NOT_DONE =
  "Wait for this step to finish to re-execute it.";

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
  canCancel: boolean;
}

interface RunActionButtonsProps {
  run?: RunActionButtonsRun;
  selectedStep: string | null;
  selectedStepState: IStepState;
  artifactsPersisted: boolean;
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
  onExecute: (stepKey?: string, resumeRetry?: boolean) => Promise<void>;
  onLaunch: (stepKey?: string, resumeRetry?: boolean) => Promise<void>;
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
        if (res.data?.cancelPipelineExecution?.message) {
          SharedToaster.show({
            message: res.data.cancelPipelineExecution.message,
            icon: "error",
            intent: Intent.DANGER
          });
        }
      }}
    />
  );
};

interface ReexecuteButtonProps {
  selectedStep?: string;
  artifactsPersisted?: boolean;
  onChangeExecutionType?: (type: ExecutionType) => void;
  onClick: (stepKey?: string, resumeRetry?: boolean) => void;
  disabled?: boolean;
  stepInFlight?: boolean;
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
  const { onClick, selectedStep, stepInFlight, artifactsPersisted } = props;

  const disabled = !selectedStep || stepInFlight || !artifactsPersisted;
  return (
    <Tooltip
      hoverOpenDelay={300}
      position={Position.LEFT}
      targetTagName="div"
      openOnTargetFocus={false}
      content={
        !artifactsPersisted
          ? REEXECUTE_SINGLE_STEP_NO_ARTIFACTS
          : !selectedStep
          ? REEXECUTE_SINGLE_STEP_NO_SELECTION
          : stepInFlight
          ? REEXECUTE_SINGLE_STEP_NOT_DONE
          : REEXECUTE_SINGLE_STEP
      }
    >
      <ReexecuteMenuItem
        text={
          selectedStep ? `Step ${selectedStep}` : REEXECUTE_SUBSET_DEFAULT_TITLE
        }
        icon="select"
        disabled={disabled}
        onClick={() => onClick(selectedStep)}
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
  selectedStep: string | null;
  artifactsPersisted: boolean;
  onClick: (stepKey?: string, resumeRetry?: boolean) => void;
  isLaunch: boolean;
  isPipelineUnknown: boolean;
  run?: RunActionButtonsRun;
  selectedStepState: IStepState;
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
}

export function ReexecuteButtonGroup(props: ReexecuteButtonGroupProps) {
  const {
    selectedStep,
    artifactsPersisted,
    onClick,
    isLaunch,
    isPipelineUnknown,
    run,
    selectedStepState,
    executionPlan
  } = props;
  // Run's status
  const isRetryDisabled = !(
    executionPlan &&
    run &&
    run.status === PipelineRunStatus.FAILURE
  );
  const stepInFlight = ![IStepState.FAILED, IStepState.SUCCEEDED].includes(
    selectedStepState
  );

  return (
    <Popover
      content={
        <Menu>
          <ReexecuteFullPipelineButton onClick={onClick} />
          <ReexecuteSubsetButton
            onClick={onClick}
            selectedStep={selectedStep || undefined}
            stepInFlight={stepInFlight}
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
          text={isLaunch ? LAUNCH_REEXECUTE_TITLE : START_REEXECUTE_TITLE}
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
  const { run, executionPlan, onExecute, onLaunch } = props;
  // TODO: temporary hack to try to force rerender of the action buttons based on
  // the local storage state.  Real solution is to push the LaunchButtonGroup to use
  // context (https://github.com/dagster-io/dagster/issues/2153)
  const [, updateState] = React.useState<ExecutionType>(ExecutionType.START);

  const isPipelineUnknown = run?.pipeline.__typename === "UnknownPipeline";
  const isReexecutionDisabled = !(
    run?.status === PipelineRunStatus.FAILURE ||
    run?.status === PipelineRunStatus.SUCCESS
  );

  return (
    <>
      <LaunchButtonGroup small={true} onChange={updateState}>
        <ExecutionStartButton
          title={START_REEXECUTE_TITLE}
          icon="repeat"
          onClick={() => {}}
          disabled={isReexecutionDisabled}
          small={true}
        >
          <ReexecuteButtonGroup
            // Re-execute button group
            onClick={onExecute}
            isLaunch={false}
            selectedStep={props.selectedStep}
            artifactsPersisted={props.artifactsPersisted}
            isPipelineUnknown={isPipelineUnknown}
            run={run}
            selectedStepState={props.selectedStepState}
            executionPlan={executionPlan}
          />
        </ExecutionStartButton>

        <ExecutionStartButton
          title={LAUNCH_REEXECUTE_TITLE}
          icon="repeat"
          onClick={() => {}}
          disabled={isReexecutionDisabled}
          small={true}
        >
          <ReexecuteButtonGroup
            // Launch re-execution button group
            onClick={onLaunch}
            isLaunch={true}
            selectedStep={props.selectedStep}
            artifactsPersisted={props.artifactsPersisted}
            isPipelineUnknown={isPipelineUnknown}
            run={run}
            selectedStepState={props.selectedStepState}
            executionPlan={executionPlan}
          />
        </ExecutionStartButton>
      </LaunchButtonGroup>
      {run?.canCancel && (
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
