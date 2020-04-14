import * as React from "react";
import * as yaml from "yaml";

import { Colors, Spinner } from "@blueprintjs/core";

import { StartPipelineExecution } from "./types/StartPipelineExecution";
import { LaunchPipelineExecution } from "./types/LaunchPipelineExecution";
import { StartPipelineReexecution } from "./types/StartPipelineReexecution";
import { LaunchPipelineReexecution } from "./types/LaunchPipelineReexecution";
import gql from "graphql-tag";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components/macro";
import { RunTableRunFragment } from "./types/RunTableRunFragment";
import { RunFragment } from "../runs/types/RunFragment";

export type IRunStatus =
  | "SUCCESS"
  | "NOT_STARTED"
  | "FAILURE"
  | "STARTED"
  | "MANAGED";

export function titleForRun(run: { runId: string }) {
  return run.runId.split("-").shift();
}

export function handleExecutionResult(
  pipelineName: string,
  result: void | {
    data?: StartPipelineExecution | LaunchPipelineExecution;
  },
  opts: { openInNewWindow: boolean }
) {
  if (!result || !result.data) {
    showCustomAlert({ body: `No data was returned. Did Dagit crash?` });
    return;
  }

  const obj = (result.data as StartPipelineExecution).startPipelineExecution
    ? (result.data as StartPipelineExecution).startPipelineExecution
    : (result.data as LaunchPipelineExecution).launchPipelineExecution;

  if (
    obj.__typename === "LaunchPipelineExecutionSuccess" ||
    obj.__typename === "StartPipelineExecutionSuccess"
  ) {
    const url = `/runs/${obj.run.pipeline.name}/${obj.run.runId}`;
    if (opts.openInNewWindow) {
      window.open(url, "_blank");
    } else {
      window.location.href = url;
    }
  } else if (obj.__typename === "PythonError") {
    console.log(obj);
    const message = `${obj.message}`;
    showCustomAlert({ body: message });
  } else if (obj.__typename === "StartPipelineExecutionDisabledError") {
    const message = `Your instance has been configured to disable local execution.  Please check
    the run launcher configuration on your dagster instance for more options.`;
    showCustomAlert({ body: message });
  } else {
    let message = `${pipelineName} cannot be executed with the provided config.`;

    if ("errors" in obj) {
      message += ` Please fix the following errors:\n\n${obj.errors
        .map(error => error.message)
        .join("\n\n")}`;
    }

    showCustomAlert({ body: message });
  }
}

export function handleReexecutionResult(
  pipelineName: string,
  result: void | {
    data?: StartPipelineReexecution | LaunchPipelineReexecution;
  },
  opts: { openInNewWindow: boolean }
) {
  if (!result || !result.data) {
    showCustomAlert({ body: `No data was returned. Did Dagit crash?` });
    return;
  }

  const obj = (result.data as StartPipelineReexecution).startPipelineReexecution
    ? (result.data as StartPipelineReexecution).startPipelineReexecution
    : (result.data as LaunchPipelineReexecution).launchPipelineReexecution;

  if (
    obj.__typename === "LaunchPipelineReexecutionSuccess" ||
    obj.__typename === "StartPipelineReexecutionSuccess"
  ) {
    const url = `/runs/${obj.run.pipeline.name}/${obj.run.runId}`;
    if (opts.openInNewWindow) {
      window.open(url, "_blank");
    } else {
      window.location.href = url;
    }
  } else if (obj.__typename === "PythonError") {
    console.log(obj);
    const message = `${obj.message}`;
    showCustomAlert({ body: message });
  } else if (obj.__typename === "StartPipelineReexecutionDisabledError") {
    const message = `Your instance has been configured to disable local execution.  Please check
    the run launcher configuration on your dagster instance for more options.`;
    showCustomAlert({ body: message });
  } else {
    let message = `${pipelineName} cannot be executed with the provided config.`;

    if ("errors" in obj) {
      message += ` Please fix the following errors:\n\n${obj.errors
        .map(error => error.message)
        .join("\n\n")}`;
    }

    showCustomAlert({ body: message });
  }
}

function getExecutionMetadata(run: RunFragment | RunTableRunFragment) {
  return {
    parentRunId: run.runId,
    rootRunId: run.rootRunId ? run.rootRunId : run.runId,
    tags: [
      ...run.tags.map(tag => ({
        key: tag.key,
        value: tag.value
      }))
    ]
  };
}

function isRunFragment(
  run: RunFragment | RunTableRunFragment
): run is RunFragment {
  return (run as RunFragment).environmentConfigYaml !== undefined;
}

export function getReexecutionVariables(input: {
  run: RunFragment | RunTableRunFragment;
  envYaml?: string;
  stepKey?: string;
  resumeRetry?: boolean;
}) {
  const { run, envYaml, stepKey, resumeRetry } = input;

  if (isRunFragment(run)) {
    if (!run || run.pipeline.__typename === "UnknownPipeline") {
      return undefined;
    }

    const executionParams = {
      mode: run.mode,
      environmentConfigData: yaml.parse(run.environmentConfigYaml),
      selector: {
        name: run.pipeline.name,
        solidSubset: run.pipeline.solids.map(s => s.name)
      }
    };

    // single step re-execution
    const { executionPlan } = run;
    if (stepKey && executionPlan) {
      const step = executionPlan.steps.find(s => s.key === stepKey);
      if (!step) return;
      executionParams["stepKeys"] = [stepKey];
      executionParams["retryRunId"] = run.runId;
    } else {
      if (resumeRetry) {
        executionParams["retryRunId"] = run.runId;
      }
    }
    executionParams["executionMetadata"] = getExecutionMetadata(run);
    return { executionParams };
  } else {
    if (!envYaml) {
      return undefined;
    }
    return {
      executionParams: {
        mode: run.mode,
        environmentConfigData: yaml.parse(envYaml),
        selector: {
          name: run.pipeline.name,
          solidSubset:
            run.pipeline.__typename === "Pipeline"
              ? run.pipeline.solids.map(s => s.name)
              : []
        },
        executionMetadata: getExecutionMetadata(run)
      }
    };
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

export const START_PIPELINE_EXECUTION_MUTATION = gql`
  mutation StartPipelineExecution($executionParams: ExecutionParams!) {
    startPipelineExecution(executionParams: $executionParams) {
      __typename
      ... on StartPipelineExecutionSuccess {
        run {
          runId
          pipeline {
            name
          }
          tags {
            key
            value
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const LAUNCH_PIPELINE_EXECUTION_MUTATION = gql`
  mutation LaunchPipelineExecution($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
      __typename
      ... on LaunchPipelineExecutionSuccess {
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const DELETE_MUTATION = gql`
  mutation Delete($runId: String!) {
    deletePipelineRun(runId: $runId) {
      __typename
      ... on PythonError {
        message
      }
      ... on PipelineRunNotFoundError {
        message
      }
    }
  }
`;

export const CANCEL_MUTATION = gql`
  mutation Cancel($runId: String!) {
    cancelPipelineExecution(runId: $runId) {
      __typename
      ... on CancelPipelineExecutionFailure {
        message
      }
      ... on PipelineRunNotFoundError {
        message
      }
      ... on CancelPipelineExecutionSuccess {
        run {
          runId
          canCancel
        }
      }
    }
  }
`;

export const START_PIPELINE_REEXECUTION_MUTATION = gql`
  mutation StartPipelineReexecution($executionParams: ExecutionParams!) {
    startPipelineReexecution(executionParams: $executionParams) {
      __typename
      ... on StartPipelineReexecutionSuccess {
        run {
          runId
          pipeline {
            name
          }
          tags {
            key
            value
          }
          rootRunId
          parentRunId
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const LAUNCH_PIPELINE_REEXECUTION_MUTATION = gql`
  mutation LaunchPipelineReexecution($executionParams: ExecutionParams!) {
    launchPipelineReexecution(executionParams: $executionParams) {
      __typename
      ... on LaunchPipelineReexecutionSuccess {
        run {
          runId
          pipeline {
            name
          }
          rootRunId
          parentRunId
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
      ... on PythonError {
        message
        stack
      }
    }
  }
`;
