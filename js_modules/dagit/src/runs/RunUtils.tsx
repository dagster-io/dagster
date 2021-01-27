import {gql} from '@apollo/client';
import {Icon, Popover} from '@blueprintjs/core';
import qs from 'query-string';
import * as React from 'react';
import * as yaml from 'yaml';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {APP_PATH_PREFIX} from 'src/app/DomUtils';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {DagsterTag} from 'src/runs/RunTag';
import {StepSelection} from 'src/runs/StepSelection';
import {TimeElapsed} from 'src/runs/TimeElapsed';
import {LaunchPipelineExecution} from 'src/runs/types/LaunchPipelineExecution';
import {LaunchPipelineReexecution} from 'src/runs/types/LaunchPipelineReexecution';
import {RunActionMenuFragment} from 'src/runs/types/RunActionMenuFragment';
import {RunFragment} from 'src/runs/types/RunFragment';
import {RunTableRunFragment} from 'src/runs/types/RunTableRunFragment';
import {RunTimeFragment} from 'src/runs/types/RunTimeFragment';
import {ExecutionParams, PipelineRunStatus} from 'src/types/globalTypes';
import {Timestamp, TimezoneContext, timestampToString} from 'src/ui/TimeComponents';
import {REPOSITORY_ORIGIN_FRAGMENT} from 'src/workspace/RepositoryInformation';

export function titleForRun(run: {runId: string}) {
  return run.runId.split('-').shift();
}

export const RunsQueryRefetchContext = React.createContext<{
  refetch: () => void;
}>({refetch: () => {}});

export function handleLaunchResult(
  pipelineName: string,
  result: void | {data?: LaunchPipelineExecution | LaunchPipelineReexecution | null},
) {
  const obj =
    result && result.data && 'launchPipelineExecution' in result.data
      ? result.data.launchPipelineExecution
      : result && result.data && 'launchPipelineReexecution' in result.data
      ? result.data.launchPipelineReexecution
      : null;

  if (!obj) {
    showCustomAlert({body: `No data was returned. Did Dagit crash?`});
    return;
  }

  if (obj.__typename === 'LaunchPipelineRunSuccess') {
    openRunInBrowser(obj.run);
  } else if (obj.__typename === 'PythonError') {
    showCustomAlert({
      title: 'Error',
      body: <PythonErrorInfo error={obj} />,
    });
  } else {
    let message = `${pipelineName} cannot be executed with the provided config.`;

    if ('errors' in obj) {
      message += ` Please fix the following errors:\n\n${obj.errors
        .map((error) => error.message)
        .join('\n\n')}`;
    }

    showCustomAlert({body: message});
  }
}

export function openRunInBrowser(
  run: {runId: string; pipelineName: string},
  opts?: {query?: {[key: string]: string}},
) {
  window.location.href = `${APP_PATH_PREFIX}/instance/runs/${run.runId}?${
    opts?.query ? qs.stringify(opts.query) : ''
  }`;
}

function getBaseExecutionMetadata(run: RunFragment | RunTableRunFragment | RunActionMenuFragment) {
  const hiddenTagKeys: string[] = [DagsterTag.IsResumeRetry, DagsterTag.StepSelection];

  return {
    parentRunId: run.runId,
    rootRunId: run.rootRunId ? run.rootRunId : run.runId,
    tags: [
      // Clean up tags related to run grouping once we decide its persistence
      // https://github.com/dagster-io/dagster/issues/2495
      ...run.tags
        .filter((tag) => !hiddenTagKeys.includes(tag.key))
        .map((tag) => ({
          key: tag.key,
          value: tag.value,
        })),
      // pass resume/retry indicator via tags
      // pass run group info via tags
      {
        key: DagsterTag.ParentRunId,
        value: run.runId,
      },
      {
        key: DagsterTag.RootRunId,
        value: run.rootRunId ? run.rootRunId : run.runId,
      },
    ],
  };
}

export type ReExecutionStyle =
  | {type: 'all'}
  | {type: 'from-failure'}
  | {type: 'selection'; selection: StepSelection};

export function getReexecutionVariables(input: {
  run: (RunFragment | RunTableRunFragment | RunActionMenuFragment) & {runConfigYaml: string};
  style: ReExecutionStyle;
  repositoryLocationName: string;
  repositoryName: string;
}) {
  const {run, style, repositoryLocationName, repositoryName} = input;

  if (!run || ('pipeline' in run && run.pipeline.__typename === 'UnknownPipeline')) {
    return undefined;
  }

  const executionParams: ExecutionParams = {
    mode: run.mode,
    runConfigData: yaml.parse(run.runConfigYaml),
    executionMetadata: getBaseExecutionMetadata(run),
    selector: {
      repositoryLocationName,
      repositoryName,
      pipelineName: 'pipelineName' in run ? run.pipelineName : run.pipeline.name,
      solidSelection: 'solidSelection' in run ? run.solidSelection : run.pipeline.solidSelection,
    },
  };

  if (style.type === 'from-failure') {
    executionParams.executionMetadata?.tags?.push({
      key: DagsterTag.IsResumeRetry,
      value: 'true',
    });
  }
  if (style.type === 'selection') {
    executionParams.stepKeys = style.selection.keys;
    executionParams.executionMetadata?.tags?.push({
      key: DagsterTag.StepSelection,
      value: style.selection.query,
    });
  }

  return {executionParams};
}

export const LAUNCH_PIPELINE_EXECUTION_MUTATION = gql`
  mutation LaunchPipelineExecution($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
      __typename
      ... on LaunchPipelineRunSuccess {
        run {
          id
          runId
          pipelineName
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

export const TERMINATE_MUTATION = gql`
  mutation Terminate($runId: String!, $terminatePolicy: TerminatePipelinePolicy) {
    terminatePipelineExecution(runId: $runId, terminatePolicy: $terminatePolicy) {
      __typename
      ... on TerminatePipelineExecutionFailure {
        message
      }
      ... on PipelineRunNotFoundError {
        message
      }
      ... on TerminatePipelineExecutionSuccess {
        run {
          id
          runId
          canTerminate
        }
      }
      ... on PythonError {
        message
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
          id
          runId
          pipelineName
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

interface RunTimeProps {
  run: RunTimeFragment;
  size?: 'standard' | 'minimal';
}
export const RunTime: React.FunctionComponent<RunTimeProps> = ({run, size}) => {
  const [timezone] = React.useContext(TimezoneContext);
  const {stats, status} = run;

  if (stats.__typename !== 'PipelineRunStatsSnapshot') {
    return (
      <Popover content={<PythonErrorInfo error={stats} />}>
        <div>
          <Icon icon="error" /> Failed to load times
        </div>
      </Popover>
    );
  }

  const useSameDayFormat =
    size === 'minimal' &&
    timezone !== 'UTC' &&
    stats.startTime &&
    timestampToString({unix: stats.startTime, format: 'MMM DD'}, timezone) ===
      timestampToString({ms: Date.now(), format: 'MMM DD'}, timezone);

  const content = () => {
    if (stats.startTime) {
      return <Timestamp unix={stats.startTime} format={useSameDayFormat ? 'h:mm A' : undefined} />;
    }

    switch (status) {
      case PipelineRunStatus.FAILURE:
        return 'Failed to start';
      case PipelineRunStatus.QUEUED:
        return 'Queued';
      case PipelineRunStatus.CANCELED:
        return 'Canceled';
      case PipelineRunStatus.CANCELING:
        return 'Canceling…';
      default:
        return 'Starting…';
    }
  };

  return <div>{content()}</div>;
};

export const RunElapsed: React.FC<RunTimeProps> = ({run}) => {
  if (run.stats.__typename !== 'PipelineRunStatsSnapshot') {
    return (
      <Popover content={<PythonErrorInfo error={run.stats} />}>
        <div>
          <Icon icon="error" /> Failed to load times
        </div>
      </Popover>
    );
  }

  return <TimeElapsed startUnix={run.stats.startTime} endUnix={run.stats.endTime} />;
};

export const RUN_TIME_FRAGMENT = gql`
  fragment RunTimeFragment on PipelineRun {
    id
    status
    stats {
      ... on PipelineRunStatsSnapshot {
        id
        startTime
        endTime
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

export const RUN_ACTION_MENU_FRAGMENT = gql`
  fragment RunActionMenuFragment on PipelineRun {
    id
    runId
    rootRunId
    pipelineName
    solidSelection
    pipelineSnapshotId
    mode
    canTerminate
    tags {
      key
      value
    }
    status
    repositoryOrigin {
      ...RepositoryOriginFragment
    }
  }
  ${REPOSITORY_ORIGIN_FRAGMENT}
`;
