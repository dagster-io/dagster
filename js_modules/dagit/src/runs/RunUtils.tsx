import * as React from "react";
import styled from "styled-components";
import { Colors, Spinner } from "@blueprintjs/core";
import gql from "graphql-tag";
import { HandleStartExecutionFragment } from "./types/HandleStartExecutionFragment";
import { showCustomAlert } from "../CustomAlertProvider";

export type IRunStatus = "SUCCESS" | "NOT_STARTED" | "FAILURE" | "STARTED";

export function titleForRun(run: { runId: string }) {
  return run.runId.split("-").shift();
}

export function handleStartExecutionResult(
  pipelineName: string,
  result: void | {
    data?: { startPipelineExecution: HandleStartExecutionFragment };
  }
) {
  if (!result || !result.data) {
    showCustomAlert({ message: `No data was returned. Did Dagit crash?` });
    return;
  }

  const obj = result.data.startPipelineExecution;

  if (obj.__typename === "StartPipelineExecutionSuccess") {
    window.open(`/${pipelineName}/runs/${obj.run.runId}`, "_blank");
  } else {
    let message = `${pipelineName} cannot not be executed with the provided config.`;

    if ("errors" in obj) {
      message += ` Please fix the following errors:\n\n${obj.errors
        .map(error => error.message)
        .join("\n\n")}`;
    }

    showCustomAlert({ message });
  }
}

export const RunStatus: React.SFC<{ status: IRunStatus }> = ({ status }) => {
  if (status === "STARTED") {
    return <Spinner size={11} />;
  }
  return <RunStatusDot status={status} />;
};

const RunStatusDot = styled.div<{
  status: IRunStatus;
}>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      NOT_STARTED: Colors.GRAY1,
      STARTED: Colors.GRAY3,
      SUCCESS: Colors.GREEN2,
      FAILURE: Colors.RED3
    }[status])};
  &:hover {
    background: ${({ status }) =>
      ({
        NOT_STARTED: Colors.GRAY1,
        STARTED: Colors.GRAY3,
        SUCCESS: Colors.GREEN2,
        FAILURE: Colors.RED5
      }[status])};
  }
`;

export const HANDLE_START_EXECUTION_FRAGMENT = gql`
  fragment HandleStartExecutionFragment on StartPipelineExecutionResult {
    __typename

    ... on StartPipelineExecutionSuccess {
      run {
        runId
      }
    }
    ... on PipelineNotFoundError {
      message
    }
    ... on PipelineConfigValidationInvalid {
      errors {
        message
      }
    }
  }
`;
