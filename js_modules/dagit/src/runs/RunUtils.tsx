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
import { RunFragment } from "./types/RunFragment";
import { RunActionMenuFragment } from "./types/RunActionMenuFragment";
import { RunTimeFragment } from "./types/RunTimeFragment";
import { unixTimestampToString } from "../Util";
import PythonErrorInfo from "../PythonErrorInfo";

import { useMutation, useLazyQuery } from "react-apollo";
import {
  Button,
  Menu,
  MenuItem,
  Popover,
  MenuDivider,
  Intent,
  Icon,
  Tooltip,
  Position
} from "@blueprintjs/core";
import { SharedToaster } from "../DomUtils";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import * as qs from "query-string";
import { Details } from "../ListComponents";
import { Link } from "react-router-dom";
import { RunStatsDetailFragment } from "./types/RunStatsDetailFragment";
import { formatElapsedTime } from "../Util";
import { REEXECUTE_PIPELINE_UNKNOWN } from "./RunActionButtons";
import { DocumentNode } from "graphql";

export type IRunStatus =
  | "SUCCESS"
  | "NOT_STARTED"
  | "FAILURE"
  | "STARTED"
  | "MANAGED";

export function titleForRun(run: { runId: string }) {
  return run.runId.split("-").shift();
}

export const RUN_STATUS_COLORS = {
  NOT_STARTED: Colors.GRAY1,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY3,
  SUCCESS: Colors.GREEN2,
  FAILURE: Colors.RED3
};
export const RUN_STATUS_HOVER_COLORS = {
  NOT_STARTED: Colors.GRAY3,
  MANAGED: Colors.GRAY3,
  STARTED: Colors.GRAY5,
  SUCCESS: Colors.GREEN4,
  FAILURE: Colors.RED5
};

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
    obj.__typename === "LaunchPipelineRunSuccess" ||
    obj.__typename === "StartPipelineRunSuccess"
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
  } else if (obj.__typename === "StartPipelineRunDisabledError") {
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
    obj.__typename === "LaunchPipelineRunSuccess" ||
    obj.__typename === "StartPipelineRunSuccess"
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
  } else if (obj.__typename === "StartPipelineRunDisabledError") {
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

function getExecutionMetadata(
  run: RunFragment | RunTableRunFragment | RunActionMenuFragment,
  resumeRetry = false,
  stepKeys: string[] = [],
  stepQuery = ""
) {
  return {
    parentRunId: run.runId,
    rootRunId: run.rootRunId ? run.rootRunId : run.runId,
    tags: [
      ...run.tags
        .filter(
          tag =>
            !(tag.key in ["dagster/is_resume_retry", "dagster/step_selection"])
        )
        .map(tag => ({
          key: tag.key,
          value: tag.value
        })),
      // pass resume/retry indicator via tags
      {
        key: "dagster/is_resume_retry",
        value: resumeRetry.toString()
      },
      // pass run group info via tags
      // https://github.com/dagster-io/dagster/issues/2495
      {
        key: "dagster/parent_run_id",
        value: run.runId
      },
      {
        key: "dagster/root_run_id",
        value: run.rootRunId ? run.rootRunId : run.runId
      },
      // pass step selection query via tags
      ...(stepKeys.length > 0 && stepQuery
        ? [
            {
              key: "dagster/step_selection",
              value: stepQuery
            }
          ]
        : [])
    ]
  };
}

function isRunFragment(
  run: RunFragment | RunTableRunFragment | RunActionMenuFragment
): run is RunFragment {
  return (run as RunFragment).environmentConfigYaml !== undefined;
}

export function getReexecutionVariables(input: {
  run: RunFragment | RunTableRunFragment | RunActionMenuFragment;
  envYaml?: string;
  stepKeys?: string[];
  stepQuery?: string;
  resumeRetry?: boolean;
}) {
  const { run, envYaml, stepKeys, resumeRetry, stepQuery } = input;

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

    // subset re-execution
    const { executionPlan } = run;
    if (stepKeys && stepKeys.length > 0 && executionPlan) {
      const step = executionPlan.steps.find(s => stepKeys.includes(s.key));
      if (!step) return;
      executionParams["stepKeys"] = stepKeys;
    }

    executionParams["executionMetadata"] = getExecutionMetadata(
      run,
      resumeRetry,
      stepKeys,
      stepQuery
    );

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

export const RunStatus: React.SFC<{ status: IRunStatus; square?: boolean }> = ({
  status,
  square
}) => {
  if (status === "STARTED") {
    return (
      <div style={{ display: "inline-block" }}>
        <Spinner size={11} />
      </div>
    );
  }
  return <RunStatusDot status={status} square={square} />;
};

// eslint-disable-next-line no-unexpected-multiline
const RunStatusDot = styled.div<{ status: IRunStatus; square?: boolean }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: ${({ square }) => (square ? 0 : 5.5)}px;
  align-self: center;
  transition: background 200ms linear;
  background: ${({ status }) => RUN_STATUS_COLORS[status]};
  &:hover {
    background: ${({ status }) => RUN_STATUS_HOVER_COLORS[status]};
  }
`;

export const START_PIPELINE_EXECUTION_MUTATION = gql`
  mutation StartPipelineExecution($executionParams: ExecutionParams!) {
    startPipelineExecution(executionParams: $executionParams) {
      __typename
      ... on StartPipelineRunSuccess {
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
      ... on LaunchPipelineRunSuccess {
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
    terminatePipelineExecution(runId: $runId) {
      __typename
      ... on TerminatePipelineExecutionFailure {
        message
      }
      ... on PipelineRunNotFoundError {
        message
      }
      ... on TerminatePipelineExecutionSuccess {
        run {
          runId
          canTerminate
        }
      }
    }
  }
`;

export const START_PIPELINE_REEXECUTION_MUTATION = gql`
  mutation StartPipelineReexecution($executionParams: ExecutionParams!) {
    startPipelineReexecution(executionParams: $executionParams) {
      __typename
      ... on StartPipelineRunSuccess {
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
      ... on LaunchPipelineRunSuccess {
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

const OPEN_PLAYGROUND_UNKNOWN =
  "Playground is unavailable because the pipeline is not present in the current repository.";

export const RunActionsMenu: React.FunctionComponent<{
  run: RunTableRunFragment | RunActionMenuFragment;
  refetchQueries: { query: DocumentNode; variables: any }[];
}> = ({ run, refetchQueries }) => {
  const [reexecute] = useMutation(START_PIPELINE_REEXECUTION_MUTATION);
  const [cancel] = useMutation(CANCEL_MUTATION, { refetchQueries });
  const [destroy] = useMutation(DELETE_MUTATION, { refetchQueries });
  const [loadEnv, { called, loading, data }] = useLazyQuery(
    PipelineEnvironmentYamlQuery,
    {
      variables: { runId: run.runId }
    }
  );

  const envYaml = data?.pipelineRunOrError?.environmentConfigYaml;
  const infoReady = run.pipeline.__typename === "Pipeline" && envYaml != null;
  return (
    <Popover
      content={
        <Menu>
          <MenuItem
            text={
              loading ? "Loading Configuration..." : "View Configuration..."
            }
            disabled={envYaml == null}
            icon="share"
            onClick={() =>
              showCustomAlert({
                title: "Config",
                body: (
                  <HighlightedCodeBlock value={envYaml} languages={["yaml"]} />
                )
              })
            }
          />
          <MenuDivider />

          <Tooltip
            content={OPEN_PLAYGROUND_UNKNOWN}
            position={Position.BOTTOM}
            disabled={infoReady}
          >
            <MenuItem
              text="Open in Playground..."
              disabled={!infoReady}
              icon="edit"
              target="_blank"
              href={`/pipeline/${
                run.pipeline.name
              }/playground/setup?${qs.stringify({
                mode: run.mode,
                config: envYaml,
                solidSubset:
                  run.pipeline.__typename === "Pipeline"
                    ? run.pipeline.solids.map(s => s.name)
                    : []
              })}`}
            />
          </Tooltip>
          <Tooltip
            content={REEXECUTE_PIPELINE_UNKNOWN}
            position={Position.BOTTOM}
            disabled={infoReady}
          >
            <MenuItem
              text="Re-execute"
              disabled={!infoReady}
              icon="repeat"
              onClick={async () => {
                const result = await reexecute({
                  variables: getReexecutionVariables({
                    run,
                    envYaml
                  })
                });
                handleReexecutionResult(run.pipeline.name, result, {
                  openInNewWindow: false
                });
              }}
            />
          </Tooltip>
          <MenuItem
            text="Cancel"
            icon="stop"
            disabled={!run.canTerminate}
            onClick={async () => {
              const result = await cancel({ variables: { runId: run.runId } });
              showToastFor(
                result.data.terminatePipelineExecution,
                "Run cancelled."
              );
            }}
          />
          <MenuDivider />
          <MenuItem
            text="Delete"
            icon="trash"
            disabled={run.canTerminate}
            onClick={async () => {
              const result = await destroy({ variables: { runId: run.runId } });
              showToastFor(result.data.deletePipelineRun, "Run deleted.");
            }}
          />
        </Menu>
      }
      position={"bottom"}
      onOpening={() => {
        if (!called) {
          loadEnv();
        }
      }}
    >
      <Button minimal={true} icon="more" />
    </Popover>
  );
};

function showToastFor(
  possibleError: { __typename: string; message?: string },
  successMessage: string
) {
  if ("message" in possibleError) {
    SharedToaster.show({
      message: possibleError.message,
      icon: "error",
      intent: Intent.DANGER
    });
  } else {
    SharedToaster.show({
      message: successMessage,
      icon: "confirm",
      intent: Intent.SUCCESS
    });
  }
}

// Avoid fetching envYaml on load in Runs page. It is slow.
const PipelineEnvironmentYamlQuery = gql`
  query PipelineEnvironmentYamlQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        environmentConfigYaml
      }
    }
  }
`;

export const RunStatsDetails = ({ run }: { run: RunStatsDetailFragment }) => {
  if (run.stats.__typename !== "PipelineRunStatsSnapshot") {
    return (
      <Popover
        content={<PythonErrorInfo error={run.stats} />}
        targetTagName="div"
      >
        <Details>
          <Icon icon="error" /> Failed to load stats
        </Details>
      </Popover>
    );
  }
  return (
    <Details>
      <Link
        to={`/runs/${run.pipeline.name}/${run.runId}?q=type:step_success`}
      >{`${run.stats.stepsSucceeded} steps succeeded, `}</Link>
      <Link to={`/runs/${run.pipeline.name}/${run.runId}?q=type:step_failure`}>
        {`${run.stats.stepsFailed} steps failed, `}{" "}
      </Link>
      <Link
        to={`/runs/${run.pipeline.name}/${run.runId}?q=type:materialization`}
      >{`${run.stats.materializations} materializations`}</Link>
      ,{" "}
      <Link
        to={`/runs/${run.pipeline.name}/${run.runId}?q=type:expectation`}
      >{`${run.stats.expectations} expectations passed`}</Link>
    </Details>
  );
};

export const RunTime = ({ run }: { run: RunTimeFragment }) => {
  if (run.stats.__typename !== "PipelineRunStatsSnapshot") {
    return (
      <Popover content={<PythonErrorInfo error={run.stats} />}>
        <div>
          <Icon icon="error" /> Failed to load times
        </div>
      </Popover>
    );
  }

  return (
    <>
      {run.stats.startTime ? (
        <div style={{ marginBottom: 4 }}>
          <Icon icon="calendar" /> {unixTimestampToString(run.stats.startTime)}
          <Icon
            icon="arrow-right"
            style={{ marginLeft: 10, marginRight: 10 }}
          />
          {unixTimestampToString(run.stats.endTime)}
        </div>
      ) : run.status === "FAILURE" ? (
        <div style={{ marginBottom: 4 }}> Failed to start</div>
      ) : (
        <div style={{ marginBottom: 4 }}>
          <Icon icon="calendar" /> Starting...
        </div>
      )}
      <TimeElapsed
        startUnix={run.stats.startTime}
        endUnix={run.stats.endTime}
      />
    </>
  );
};

export class TimeElapsed extends React.Component<{
  startUnix: number | null;
  endUnix: number | null;
}> {
  _interval?: NodeJS.Timer;
  _timeout?: NodeJS.Timer;

  componentDidMount() {
    if (this.props.endUnix) return;

    // align to the next second and then update every second so the elapsed
    // time "ticks" up. Our render method uses Date.now(), so all we need to
    // do is force another React render. We could clone the time into React
    // state but that is a bit messier.
    setTimeout(() => {
      this.forceUpdate();
      this._interval = setInterval(() => this.forceUpdate(), 1000);
    }, Date.now() % 1000);
  }

  componentWillUnmount() {
    if (this._timeout) clearInterval(this._timeout);
    if (this._interval) clearInterval(this._interval);
  }

  render() {
    const start = this.props.startUnix ? this.props.startUnix * 1000 : 0;
    const end = this.props.endUnix ? this.props.endUnix * 1000 : Date.now();

    return (
      <div>
        <Icon icon="time" /> {start ? formatElapsedTime(end - start) : ""}
      </div>
    );
  }
}

export const RunComponentFragments = {
  STATS_DETAIL_FRAGMENT: gql`
    fragment RunStatsDetailFragment on PipelineRun {
      runId
      pipeline {
        ... on PipelineReference {
          name
        }
      }
      stats {
        ... on PipelineRunStatsSnapshot {
          stepsSucceeded
          stepsFailed
          expectations
          materializations
        }
        ... on PythonError {
          ...PythonErrorFragment
        }
      }
    }
    ${PythonErrorInfo.fragments.PythonErrorFragment}
  `,
  RUN_TIME_FRAGMENT: gql`
    fragment RunTimeFragment on PipelineRun {
      status
      stats {
        ... on PipelineRunStatsSnapshot {
          startTime
          endTime
        }
        ... on PythonError {
          ...PythonErrorFragment
        }
      }
    }
    ${PythonErrorInfo.fragments.PythonErrorFragment}
  `,
  RUN_ACTION_MENU_FRAGMENT: gql`
    fragment RunActionMenuFragment on PipelineRun {
      runId
      rootRunId
      pipeline {
        __typename
        ... on PipelineReference {
          name
        }
        ... on Pipeline {
          pipelineSnapshotId
          solids {
            name
          }
        }
      }
      mode
      canTerminate
      tags {
        key
        value
      }
    }
  `
};
