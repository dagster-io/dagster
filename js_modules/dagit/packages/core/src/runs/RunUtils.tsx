import {gql} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {Timestamp} from '../app/time/Timestamp';
import {ExecutionParams, RunStatus} from '../types/globalTypes';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {Popover} from '../ui/Popover';

import {DagsterTag} from './RunTag';
import {StepSelection} from './StepSelection';
import {TimeElapsed} from './TimeElapsed';
import {LaunchPipelineExecution} from './types/LaunchPipelineExecution';
import {LaunchPipelineReexecution} from './types/LaunchPipelineReexecution';
import {RunFragment} from './types/RunFragment';
import {RunTableRunFragment} from './types/RunTableRunFragment';
import {RunTimeFragment} from './types/RunTimeFragment';

export function titleForRun(run: {runId: string}) {
  return run.runId.split('-').shift();
}

export const RunsQueryRefetchContext = React.createContext<{
  refetch: () => void;
}>({refetch: () => {}});

export function useDidLaunchEvent(cb: () => void) {
  React.useEffect(() => {
    document.addEventListener('run-launched', cb);
    return () => {
      document.removeEventListener('run-launched', cb);
    };
  }, [cb]);
}

export function handleLaunchResult(
  basePath: string,
  pipelineName: string,
  result: void | {data?: LaunchPipelineExecution | LaunchPipelineReexecution | null},
  openInTab?: boolean,
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

  if (obj.__typename === 'LaunchRunSuccess') {
    const url = `${basePath}/instance/runs/${obj.run.runId}`;
    if (openInTab) {
      window.open(url, '_blank');
    } else {
      window.location.href = url;
    }
    document.dispatchEvent(new CustomEvent('run-launched'));
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

function getBaseExecutionMetadata(run: RunFragment | RunTableRunFragment) {
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
  run: (RunFragment | RunTableRunFragment) & {runConfig: any};
  style: ReExecutionStyle;
  repositoryLocationName: string;
  repositoryName: string;
}) {
  const {run, style, repositoryLocationName, repositoryName} = input;

  if (!run || !run.pipelineSnapshotId) {
    return undefined;
  }

  const executionParams: ExecutionParams = {
    mode: run.mode,
    runConfigData: run.runConfig,
    executionMetadata: getBaseExecutionMetadata(run),
    selector: {
      repositoryLocationName,
      repositoryName,
      pipelineName: run.pipelineName,
      solidSelection: run.solidSelection,
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
      ... on LaunchRunSuccess {
        run {
          id
          runId
          pipelineName
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on RunConfigValidationInvalid {
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
      ... on UnauthorizedError {
        message
      }
      ... on RunNotFoundError {
        message
      }
    }
  }
`;

export const TERMINATE_MUTATION = gql`
  mutation Terminate($runId: String!, $terminatePolicy: TerminateRunPolicy) {
    terminatePipelineExecution(runId: $runId, terminatePolicy: $terminatePolicy) {
      __typename
      ... on TerminateRunFailure {
        message
      }
      ... on RunNotFoundError {
        message
      }
      ... on TerminateRunSuccess {
        run {
          id
          runId
          canTerminate
        }
      }
      ... on UnauthorizedError {
        message
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
      ... on LaunchRunSuccess {
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
      ... on RunConfigValidationInvalid {
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
}

export const RunTime: React.FC<RunTimeProps> = React.memo(({run}) => {
  const {stats} = run;

  if (stats.__typename !== 'RunStatsSnapshot') {
    return (
      <Popover content={<PythonErrorInfo error={stats} />}>
        <Group direction="row" spacing={4} alignItems="center">
          <IconWIP name="error" color={ColorsWIP.Red500} />
          <div>Failed to load times</div>
        </Group>
      </Popover>
    );
  }

  const content = () => {
    if (stats.startTime) {
      return <Timestamp timestamp={{unix: stats.startTime}} />;
    }
    if (stats.launchTime) {
      return <Timestamp timestamp={{unix: stats.launchTime}} />;
    }
    if (stats.enqueuedTime) {
      return <Timestamp timestamp={{unix: stats.enqueuedTime}} />;
    }

    switch (run.status) {
      case RunStatus.FAILURE:
        return 'Failed to start';
      case RunStatus.CANCELED:
        return 'Canceled';
      case RunStatus.CANCELING:
        return 'Canceling…';
      default:
        return 'Starting…';
    }
  };

  return <div>{content()}</div>;
});

export const RunElapsed: React.FC<RunTimeProps> = React.memo(({run}) => {
  if (run.stats.__typename !== 'RunStatsSnapshot') {
    return (
      <Popover content={<PythonErrorInfo error={run.stats} />}>
        <Group direction="row" spacing={4} alignItems="center">
          <IconWIP name="error" color={ColorsWIP.Red500} />
          <div>Failed to load times</div>
        </Group>
      </Popover>
    );
  }

  return <TimeElapsed startUnix={run.stats.startTime} endUnix={run.stats.endTime} />;
});

export const RUN_TIME_FRAGMENT = gql`
  fragment RunTimeFragment on Run {
    id
    status
    stats {
      ... on RunStatsSnapshot {
        id
        enqueuedTime
        launchTime
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
