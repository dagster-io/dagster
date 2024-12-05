import {History} from 'history';
import qs from 'qs';
import {createContext, memo, useEffect} from 'react';

import {DagsterTag} from './RunTag';
import {StepSelection} from './StepSelection';
import {TimeElapsed} from './TimeElapsed';
import {RunFragment} from './types/RunFragments.types';
import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {
  LaunchMultipleRunsMutation,
  LaunchPipelineExecutionMutation,
  RunTimeFragment,
} from './types/RunUtils.types';
import {Mono} from '../../../ui-components/src';
import {gql} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {Timestamp} from '../app/time/Timestamp';
import {asAssetCheckHandleInput, asAssetKeyInput} from '../assets/asInput';
import {AssetKey} from '../assets/types';
import {ExecutionParams, RunStatus} from '../graphql/types';

export function titleForRun(run: {id: string}) {
  return run.id.split('-').shift();
}

export function assetKeysForRun(run: {
  assetSelection: {path: string[]}[] | null;
  stepKeysToExecute: string[] | null;
}): AssetKey[] {
  // Note: The fallback logic here is only necessary for Dagster <0.15.0 and should be removed
  // soon, because stepKeysToExecute and asset keys do not map 1:1 for multi-component asset
  // paths.
  return run.assetSelection || run.stepKeysToExecute?.map((s) => ({path: [s]})) || [];
}

export function linkToRunEvent(
  run: {id: string},
  event: {timestamp?: string | number; stepKey: string | null},
) {
  return `/runs/${run.id}?${qs.stringify({
    focusedTime: event.timestamp ? Number(event.timestamp) : undefined,
    selection: event.stepKey,
    logs: event.stepKey ? `step:${event.stepKey}` : '',
  })}`;
}

export const RunsQueryRefetchContext = createContext<{
  refetch: () => void;
}>({refetch: () => {}});

export function useDidLaunchEvent(cb: () => void, delay = 1500) {
  useEffect(() => {
    const handler = () => {
      setTimeout(cb, delay);
    };
    document.addEventListener('run-launched', handler);
    return () => {
      document.removeEventListener('run-launched', handler);
    };
  }, [cb, delay]);
}

export type LaunchBehavior = 'open' | 'toast';

export async function handleLaunchResult(
  pipelineName: string,
  result: void | null | LaunchPipelineExecutionMutation['launchPipelineExecution'],
  history: History<unknown>,
  options: {behavior: LaunchBehavior; preserveQuerystring?: boolean},
) {
  if (!result) {
    showCustomAlert({body: `No data was returned. Did dagster-webserver crash?`});
    return;
  }

  if (result.__typename === 'LaunchRunSuccess') {
    const pathname = `/runs/${result.run.id}`;
    const search = options.preserveQuerystring ? history.location.search : '';
    const openInSameTab = () => history.push({pathname, search});

    if (options.behavior === 'open') {
      openInSameTab();
    } else {
      await showSharedToaster({
        intent: 'success',
        message: (
          <div>
            Launched run <Mono>{result.run.id.slice(0, 8)}</Mono>
          </div>
        ),
        action: {
          text: 'View',
          href: history.createHref({pathname, search}),
        },
      });
    }
    document.dispatchEvent(new CustomEvent('run-launched'));
  } else if (result.__typename === 'InvalidSubsetError') {
    showCustomAlert({body: result.message});
  } else if (result.__typename === 'PythonError') {
    showCustomAlert({
      title: 'Error',
      body: <PythonErrorInfo error={result} />,
    });
  } else {
    let message = `${pipelineName} cannot be executed with the provided config.`;

    if ('errors' in result) {
      message += ` Please fix the following errors:\n\n${result.errors
        .map((error: {message: any}) => error.message)
        .join('\n\n')}`;
    }

    showCustomAlert({body: message});
  }
}

export async function handleLaunchMultipleResult(
  result: void | null | LaunchMultipleRunsMutation['launchMultipleRuns'],
  history: History<unknown>,
  options: {behavior: LaunchBehavior; preserveQuerystring?: boolean},
) {
  if (!result) {
    showCustomAlert({body: `No data was returned. Did dagster-webserver crash?`});
    return;
  }
  const successfulRunIds: string[] = [];
  const failedRunsErrors: {message: string}[] = [];

  if (result.__typename === 'PythonError') {
    // if launch multiple runs errors out, show the PythonError and return
    showCustomAlert({
      title: 'Error',
      body: <PythonErrorInfo error={result} />,
    });
    return;
  } else if (result.__typename === 'LaunchMultipleRunsResult') {
    // show corresponding toasts
    const launchMultipleRunsResult = result.launchMultipleRunsResult;

    for (const individualResult of launchMultipleRunsResult) {
      if (individualResult.__typename === 'LaunchRunSuccess') {
        successfulRunIds.push(individualResult.run.id);

        const pathname = `/runs/${individualResult.run.id}`;
        const search = options.preserveQuerystring ? history.location.search : '';
        const openInSameTab = () => history.push({pathname, search});

        // using open with multiple runs will spam new tabs
        if (options.behavior === 'open') {
          openInSameTab();
        }
      } else if (individualResult.__typename === 'PythonError') {
        failedRunsErrors.push({message: individualResult.message});
      } else {
        let message = `Error launching run.`;
        if (
          individualResult &&
          typeof individualResult === 'object' &&
          'errors' in individualResult
        ) {
          const errors = individualResult.errors as {message: string}[];
          message += ` Please fix the following errors:\n\n${errors
            .map((error) => error.message)
            .join('\n\n')}`;
        }
        if (
          individualResult &&
          typeof individualResult === 'object' &&
          'message' in individualResult
        ) {
          message += `\n\n${individualResult.message}`;
        }

        failedRunsErrors.push({message});
      }
    }
  }
  document.dispatchEvent(new CustomEvent('run-launched'));

  // link to runs page filtered to run IDs
  const params = new URLSearchParams();
  successfulRunIds.forEach((id) => params.append('q[]', `id:${id}`));

  const queryString = `/runs?${params.toString()}`;
  history.push(queryString);

  await showSharedToaster({
    intent: 'success',
    message: <div>Launched {successfulRunIds.length} runs</div>,
    action: {
      text: 'View',
      href: history.createHref({pathname: queryString}),
    },
  });

  // show list of errors that occurred
  if (failedRunsErrors.length > 0) {
    showCustomAlert({body: failedRunsErrors.map((e) => e.message).join('\n\n')});
  }
}

function getBaseExecutionMetadata(run: RunFragment | RunTableRunFragment) {
  const hiddenTagKeys: string[] = [DagsterTag.IsResumeRetry, DagsterTag.StepSelection];

  return {
    parentRunId: run.id,
    rootRunId: run.rootRunId ? run.rootRunId : run.id,
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
        value: run.id,
      },
      {
        key: DagsterTag.RootRunId,
        value: run.rootRunId ? run.rootRunId : run.id,
      },
    ],
  };
}

export function getReexecutionParamsForSelection(input: {
  run: (RunFragment | RunTableRunFragment) & {runConfigYaml: string};
  selection: StepSelection;
  repositoryLocationName: string;
  repositoryName: string;
}) {
  const {run, selection, repositoryLocationName, repositoryName} = input;

  const executionParams: ExecutionParams = {
    mode: run.mode,
    runConfigData: run.runConfigYaml,
    executionMetadata: getBaseExecutionMetadata(run),
    selector: {
      repositoryLocationName,
      repositoryName,
      pipelineName: run.pipelineName,
      solidSelection: run.solidSelection,
      assetSelection: run.assetSelection ? run.assetSelection.map(asAssetKeyInput) : [],
      assetCheckSelection: run.assetCheckSelection
        ? run.assetCheckSelection.map(asAssetCheckHandleInput)
        : [],
    },
  };

  executionParams.stepKeys = selection.keys;
  executionParams.executionMetadata?.tags?.push({
    key: DagsterTag.StepSelection,
    value: selection.query,
  });

  return executionParams;
}

export const LAUNCH_PIPELINE_EXECUTION_MUTATION = gql`
  mutation LaunchPipelineExecution($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
      ... on LaunchRunSuccess {
        run {
          id
          pipelineName
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on RunConfigValidationInvalid {
        errors {
          message
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const LAUNCH_MULTIPLE_RUNS_MUTATION = gql`
  mutation LaunchMultipleRuns($executionParamsList: [ExecutionParams!]!) {
    launchMultipleRuns(executionParamsList: $executionParamsList) {
      __typename
      ... on LaunchMultipleRunsResult {
        launchMultipleRunsResult {
          __typename
          ... on InvalidStepError {
            invalidStepKey
          }
          ... on InvalidOutputError {
            stepKey
            invalidOutputName
          }
          ... on LaunchRunSuccess {
            run {
              id
              pipeline {
                name
              }
              tags {
                key
                value
              }
              status
              runConfigYaml
              mode
              resolvedOpSelection
            }
          }
          ... on ConflictingExecutionParamsError {
            message
          }
          ... on PresetNotFoundError {
            preset
            message
          }
          ... on RunConfigValidationInvalid {
            pipelineName
            errors {
              __typename
              message
              path
              reason
            }
          }
          ... on PipelineNotFoundError {
            message
            pipelineName
          }
          ...PythonErrorFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

export const DELETE_MUTATION = gql`
  mutation Delete($runId: String!) {
    deletePipelineRun(runId: $runId) {
      ... on UnauthorizedError {
        message
      }
      ... on RunNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const TERMINATE_MUTATION = gql`
  mutation Terminate($runIds: [String!]!, $terminatePolicy: TerminateRunPolicy) {
    terminateRuns(runIds: $runIds, terminatePolicy: $terminatePolicy) {
      ...PythonErrorFragment
      ... on TerminateRunsResult {
        terminateRunResults {
          ...PythonErrorFragment
          ... on RunNotFoundError {
            message
          }
          ... on UnauthorizedError {
            message
          }
          ... on TerminateRunFailure {
            message
          }
          ... on TerminateRunSuccess {
            run {
              id
              canTerminate
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

export const LAUNCH_PIPELINE_REEXECUTION_MUTATION = gql`
  mutation LaunchPipelineReexecution(
    $executionParams: ExecutionParams
    $reexecutionParams: ReexecutionParams
  ) {
    launchPipelineReexecution(
      executionParams: $executionParams
      reexecutionParams: $reexecutionParams
    ) {
      ... on LaunchRunSuccess {
        run {
          id
          pipelineName
          rootRunId
          parentRunId
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on RunConfigValidationInvalid {
        errors {
          message
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

interface RunTimeProps {
  run: RunTimeFragment;
}

export const RunTime = memo(({run}: RunTimeProps) => {
  const {creationTime} = run;

  return (
    <div>
      <Timestamp timestamp={{unix: creationTime}} />
    </div>
  );
});

export const RunStateSummary = memo(({run}: RunTimeProps) => {
  // kind of a hack, but we manually set the start time to the end time in the graphql resolver
  // for this case, so check for start/end time equality for the failed to start condition
  const failedToStart =
    run.status === RunStatus.FAILURE && (!run.startTime || run.startTime === run.endTime);

  return failedToStart ? (
    <div>Failed to start</div>
  ) : run.status === RunStatus.CANCELED ? (
    <div>Canceled</div>
  ) : run.status === RunStatus.CANCELING ? (
    <div>Canceling…</div>
  ) : run.status === RunStatus.QUEUED ? (
    <div>Queued…</div>
  ) : !run.startTime ? (
    <div>Starting…</div>
  ) : (
    <TimeElapsed startUnix={run.startTime} endUnix={run.endTime} />
  );
});

export const RUN_TIME_FRAGMENT = gql`
  fragment RunTimeFragment on Run {
    id
    status
    creationTime
    startTime
    endTime
    updateTime
  }
`;
