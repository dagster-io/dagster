import * as React from "react";

import { Colors, Spinner } from "@blueprintjs/core";

import { HandleStartExecutionFragment } from "./types/HandleStartExecutionFragment";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components";

export type IRunStatus =
  | "SUCCESS"
  | "NOT_STARTED"
  | "FAILURE"
  | "STARTED"
  | "MANAGED";

export function titleForRun(run: { runId: string }) {
  return run.runId.split("-").shift();
}

export function handleStartExecutionResult(
  pipelineName: string,
  result: void | {
    data?: { startPipelineExecution: HandleStartExecutionFragment };
  },
  opts: { openInNewWindow: boolean }
) {
  if (!result || !result.data) {
    showCustomAlert({ body: `No data was returned. Did Dagit crash?` });
    return;
  }

  const obj = result.data.startPipelineExecution;

  if (obj.__typename === "StartPipelineExecutionSuccess") {
    const url = `/p/${obj.run.pipeline.name}/runs/${obj.run.runId}`;
    if (opts.openInNewWindow) {
      window.open(url, "_blank");
    } else {
      window.location.href = url;
    }
  } else {
    let message = `${pipelineName} cannot not be executed with the provided config.`;

    if ("errors" in obj) {
      message += ` Please fix the following errors:\n\n${obj.errors
        .map(error => error.message)
        .join("\n\n")}`;
    }

    showCustomAlert({ body: message });
  }
}

export const RunStatus: React.SFC<{ status: IRunStatus }> = ({ status }) => {
  if (status === "STARTED") {
    return (
      <div style={{ display: "inline-block" }}>
        <Spinner size={11} />
      </div>
    );
  }
  return <RunStatusDot status={status} />;
};

// eslint-disable-next-line no-unexpected-multiline
const RunStatusDot = styled.div<{ status: IRunStatus }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) =>
    ({
      NOT_STARTED: Colors.GRAY1,
      MANAGED: Colors.GRAY3,
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
        pipeline {
          name
        }
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

export const REEXECUTE_MUTATION = gql`
  mutation Reexecute(
    $executionParams: ExecutionParams!
    $reexecutionConfig: ReexecutionConfig
  ) {
    startPipelineExecution(
      executionParams: $executionParams
      reexecutionConfig: $reexecutionConfig
    ) {
      ...HandleStartExecutionFragment
    }
  }

  ${HANDLE_START_EXECUTION_FRAGMENT}
`;
