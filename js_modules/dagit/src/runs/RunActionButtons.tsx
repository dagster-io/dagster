import * as React from "react";
import { IconNames } from "@blueprintjs/icons";
import { Button, Intent } from "@blueprintjs/core";
import { useMutation } from "react-apollo";
import { LaunchButtonDropdown, LaunchButtonConfiguration } from "../execute/LaunchButton";
import { PipelineRunStatus } from "../types/globalTypes";

import { CANCEL_MUTATION } from "./RunUtils";
import { SharedToaster } from "../DomUtils";
import { IStepState } from "../RunMetadataProvider";

const CANCEL_TITLE = "Terminate";

// Titles of re-execute options
const REEXECUTE_FULL_PIPELINE_TITLE = "Full Pipeline";
const REEXECUTE_SUBSET_NO_SELECTION_TITLE = "Step Not Selected";
const REEXECUTE_SUBSET_TITLE = `Selected Step Subset`;
const REEXECUTE_FROM_FAILURE_TITLE = "From Failure";

// Descriptions of re-execute options
export const REEXECUTE_PIPELINE_UNKNOWN =
  "Re-execute is unavailable because the pipeline is not present in the current repository.";

const REEXECUTE_FULL_PIPELINE_DESCRIPTION = "Re-execute the pipeline run from scratch";

const REEXECUTE_SUBSET = "Re-run the following steps with existing configuration:";
const REEXECUTE_SUBSET_NO_SELECTION =
  "Re-execute is only enabled when steps are selected. Try selecting a step or typing a step subset to re-execute.";
const REEXECUTE_SUBSET_NO_ARTIFACTS =
  "Use a persisting storage mode such as 'filesystem' to enable step re-execution";
const REEXECUTE_SUBSET_NOT_DONE = "Wait for the selected steps to finish to re-execute it.";

const RETRY_DESCRIPTION = "Retry the pipeline run, skipping steps that completed successfully";
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

export const RunActionButtons: React.FunctionComponent<RunActionButtonsProps> = ({
  selectedSteps,
  artifactsPersisted,
  onLaunch,
  run,
  selectedStepStates,
  executionPlan
}) => {
  // Run's status

  const isPipelineUnknown = run?.pipeline.__typename === "UnknownPipeline";
  const isSelectionPresent = selectedSteps && selectedSteps.length > 0;
  const isSelectionFinished = selectedStepStates.every(stepState =>
    [IStepState.FAILED, IStepState.SUCCEEDED].includes(stepState)
  );
  const isFinalStatus =
    run?.status === PipelineRunStatus.FAILURE || run?.status === PipelineRunStatus.SUCCESS;
  const isFailedWithPlan = executionPlan && run && run.status === PipelineRunStatus.FAILURE;

  const options: LaunchButtonConfiguration[] = [
    {
      title: REEXECUTE_FULL_PIPELINE_TITLE,
      tooltip: REEXECUTE_FULL_PIPELINE_DESCRIPTION,
      icon: "repeat",
      disabled: isPipelineUnknown || !isFinalStatus,
      onClick: () => onLaunch()
    },
    {
      title: isSelectionPresent ? REEXECUTE_SUBSET_TITLE : REEXECUTE_SUBSET_NO_SELECTION_TITLE,
      disabled:
        isPipelineUnknown || !isSelectionPresent || !isSelectionFinished || !artifactsPersisted,
      tooltip: (
        <div>
          {!artifactsPersisted
            ? REEXECUTE_SUBSET_NO_ARTIFACTS
            : !isSelectionPresent
            ? REEXECUTE_SUBSET_NO_SELECTION
            : !isSelectionFinished
            ? REEXECUTE_SUBSET_NOT_DONE
            : REEXECUTE_SUBSET}
          <div style={{ paddingLeft: "10px" }}>
            {isSelectionPresent &&
              selectedSteps.map(step => (
                <span key={step} style={{ display: "block" }}>{`* ${step}`}</span>
              ))}
          </div>
        </div>
      ),
      icon: "select",
      onClick: () => onLaunch(selectedSteps)
    },
    {
      title: REEXECUTE_FROM_FAILURE_TITLE,
      icon: "play",
      disabled: isPipelineUnknown || !isFailedWithPlan || !artifactsPersisted,
      tooltip: !artifactsPersisted
        ? RETRY_NO_ARTIFACTS
        : !isFailedWithPlan
        ? RETRY_DISABLED
        : RETRY_DESCRIPTION,
      onClick: () => onLaunch(undefined, true)
    }
  ];

  return (
    <>
      <LaunchButtonDropdown small={true} options={options} title="Launch Re-execution" />
      {run?.canTerminate && (
        <>
          <div style={{ minWidth: 6 }} />
          <CancelRunButton run={run} />
        </>
      )}
    </>
  );
};
