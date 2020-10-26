import {gql} from '@apollo/client';
import {Icon, Popover} from '@blueprintjs/core';
import * as React from 'react';
import * as yaml from 'yaml';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {APP_PATH_PREFIX} from 'src/DomUtils';
import {filterByQuery} from 'src/GraphQueryImpl';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {Timestamp, TimezoneContext, timestampToString} from 'src/TimeComponents';
import {formatElapsedTime} from 'src/Util';
import {toGraphQueryItems} from 'src/gaant/toGraphQueryItems';
import {StepSelection} from 'src/runs/StepSelection';
import {LaunchPipelineExecution} from 'src/runs/types/LaunchPipelineExecution';
import {LaunchPipelineReexecution} from 'src/runs/types/LaunchPipelineReexecution';
import {RunActionMenuFragment} from 'src/runs/types/RunActionMenuFragment';
import {RunFragment} from 'src/runs/types/RunFragment';
import {RunTableRunFragment} from 'src/runs/types/RunTableRunFragment';
import {RunTimeFragment} from 'src/runs/types/RunTimeFragment';
import {ExecutionParams} from 'src/types/globalTypes';

export function subsetTitleForRun(run: {tags: {key: string; value: string}[]}) {
  const stepsTag = run.tags.find((t) => t.key === 'dagster/step_selection');
  return stepsTag ? stepsTag.value : 'Full Pipeline';
}

export function titleForRun(run: {runId: string}) {
  return run.runId.split('-').shift();
}

export const RunsQueryRefetchContext = React.createContext<{
  refetch: () => void;
}>({refetch: () => {}});

export function handleLaunchResult(
  pipelineName: string,
  result: void | {data?: LaunchPipelineExecution | LaunchPipelineReexecution | null},
  opts: {openInNewWindow: boolean},
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
    openRunInBrowser(obj.run, opts);
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
  opts: {openInNewWindow: boolean},
) {
  const url = `${APP_PATH_PREFIX}/pipeline/${run.pipelineName}/runs/${run.runId}`;
  if (opts.openInNewWindow) {
    window.open(url, '_blank');
  } else {
    window.location.href = url;
  }
}

function getBaseExecutionMetadata(run: RunFragment | RunTableRunFragment | RunActionMenuFragment) {
  return {
    parentRunId: run.runId,
    rootRunId: run.rootRunId ? run.rootRunId : run.runId,
    tags: [
      // Clean up tags related to run grouping once we decide its persistence
      // https://github.com/dagster-io/dagster/issues/2495
      ...run.tags
        .filter((tag) => !['dagster/is_resume_retry', 'dagster/step_selection'].includes(tag.key))
        .map((tag) => ({
          key: tag.key,
          value: tag.value,
        })),
      // pass resume/retry indicator via tags
      // pass run group info via tags
      {
        key: 'dagster/parent_run_id',
        value: run.runId,
      },
      {
        key: 'dagster/root_run_id',
        value: run.rootRunId ? run.rootRunId : run.runId,
      },
    ],
  };
}

export type ReExecutionStyle =
  | {type: 'all'}
  | {type: 'from-failure'}
  | {type: 'selection'; selection: StepSelection}
  | {type: 'from-selected'; selection: StepSelection};

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
      key: 'dagster/is_resume_retry',
      value: 'true',
    });
  }
  if (style.type === 'selection') {
    executionParams.stepKeys = style.selection.keys;
    executionParams.executionMetadata?.tags?.push({
      key: 'dagster/step_selection',
      value: style.selection.query,
    });
  }
  if (style.type === 'from-selected') {
    if (!('executionPlan' in run) || !run.executionPlan) {
      console.warn('Run execution plan must be present to launch from-selected execution');
      return undefined;
    }
    const selectionAndDownstreamQuery = style.selection.keys.map((k) => `${k}*`).join(',');
    const graph = toGraphQueryItems(run.executionPlan);
    const graphFiltered = filterByQuery(graph, selectionAndDownstreamQuery);

    executionParams.stepKeys = graphFiltered.all.map((node) => node.name);
    executionParams.executionMetadata?.tags?.push({
      key: 'dagster/step_selection',
      value: selectionAndDownstreamQuery,
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

  if (run.stats.__typename !== 'PipelineRunStatsSnapshot') {
    return (
      <Popover content={<PythonErrorInfo error={run.stats} />}>
        <div>
          <Icon icon="error" /> Failed to load times
        </div>
      </Popover>
    );
  }

  const useSameDayFormat =
    size === 'minimal' &&
    timezone !== 'UTC' &&
    run.stats.startTime &&
    timestampToString({unix: run.stats.startTime, format: 'MMM DD'}, timezone) ===
      timestampToString({ms: Date.now(), format: 'MMM DD'}, timezone);

  return (
    <div>
      {run.stats.startTime ? (
        <Timestamp unix={run.stats.startTime} format={useSameDayFormat ? 'h:mm A' : undefined} />
      ) : run.status === 'FAILURE' ? (
        <>Failed to start</>
      ) : (
        <>Starting...</>
      )}
    </div>
  );
};

export const RunElapsed: React.FunctionComponent<RunTimeProps> = ({run}) => {
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

export class TimeElapsed extends React.Component<{
  startUnix: number | null;
  endUnix: number | null;
}> {
  _interval?: NodeJS.Timer;
  _timeout?: NodeJS.Timer;

  componentDidMount() {
    if (this.props.endUnix) {
      return;
    }

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
    if (this._timeout) {
      clearInterval(this._timeout);
    }
    if (this._interval) {
      clearInterval(this._interval);
    }
  }

  render() {
    const start = this.props.startUnix ? this.props.startUnix * 1000 : 0;
    const end = this.props.endUnix ? this.props.endUnix * 1000 : Date.now();

    return (
      <div>
        <Icon icon="time" iconSize={13} style={{paddingBottom: 1}} />{' '}
        {start ? formatElapsedTime(end - start) : ''}
      </div>
    );
  }
}

export const RunComponentFragments = {
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
      pipelineName
      solidSelection
      pipelineSnapshotId
      mode
      canTerminate
      tags {
        key
        value
      }
    }
  `,
};
