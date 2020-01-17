import * as React from "react";
import { IconNames } from "@blueprintjs/icons";
import { Button, Intent, Tooltip, Position } from "@blueprintjs/core";
import { useMutation } from "react-apollo";
import ExecutionStartButton from "../execute/ExecutionStartButton";
import { PipelineRunStatus } from "../types/globalTypes";

import { CANCEL_MUTATION } from "./RunUtils";
import { SharedToaster } from "../DomUtils";

const REEXECUTE_DESCRIPTION = "Re-execute the pipeline run from scratch";
const REEXECUTE_PIPELINE_UNKNOWN =
  "Re-execute is unavailable because the pipeline is not present in the current repository.";
const RETRY_DESCRIPTION =
  "Retries the pipeline run, skipping steps that completed successfully";
const RETRY_DISABLED =
  "Retries are only enabled on persistent storage. Try rerunning with a different storage configuration.";
const RETRY_PIPELINE_UNKNOWN =
  "Retry is unavailable because the pipeline is not present in the current repository.";

interface RunActionButtonsRun {
  runId: string;
  status: PipelineRunStatus;
  pipeline: {
    __typename: string;
  };
  canCancel: boolean;
  executionPlan: {
    artifactsPersisted: boolean;
  } | null;
}

interface RunActionButtonsProps {
  run?: RunActionButtonsRun;
  onReexecute: (stepKey?: string, resumeRetry?: boolean) => Promise<void>;
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
      text="Terminate"
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

export const RunActionButtons: React.FunctionComponent<RunActionButtonsProps> = props => {
  const { run, onReexecute } = props;
  const isUnknown = run?.pipeline.__typename === "UnknownPipeline";

  return (
    <>
      <Tooltip
        hoverOpenDelay={300}
        position={Position.BOTTOM}
        content={isUnknown ? REEXECUTE_PIPELINE_UNKNOWN : REEXECUTE_DESCRIPTION}
      >
        <ExecutionStartButton
          title="Re-execute"
          icon={IconNames.REPEAT}
          small={true}
          disabled={isUnknown}
          onClick={() => onReexecute()}
        />
      </Tooltip>
      {run?.canCancel && (
        <>
          <div style={{ minWidth: 6 }} />
          <CancelRunButton run={run} />
        </>
      )}
      {run?.executionPlan &&
        run.status === PipelineRunStatus.FAILURE &&
        (run.executionPlan.artifactsPersisted ? (
          <Tooltip
            hoverOpenDelay={300}
            content={isUnknown ? RETRY_PIPELINE_UNKNOWN : RETRY_DESCRIPTION}
            position={Position.BOTTOM}
          >
            <ExecutionStartButton
              title="Resume / Retry"
              icon={IconNames.REPEAT}
              small={true}
              disabled={isUnknown}
              onClick={() => onReexecute(undefined, true)}
            />
          </Tooltip>
        ) : (
          <Tooltip
            hoverOpenDelay={300}
            content={RETRY_DISABLED}
            position={Position.BOTTOM}
          >
            <ExecutionStartButton
              title="Resume / Retry"
              icon={IconNames.DISABLE}
              small={true}
              disabled
              onClick={() => null}
            />
          </Tooltip>
        ))}
    </>
  );
};
