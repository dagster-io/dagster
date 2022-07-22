import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {
  IExecutionSession,
  applyCreateSession,
  useExecutionSessionStorage,
} from '../app/ExecutionSessionStorage';
import {usePermissions} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {LaunchpadSessionError} from './LaunchpadSessionError';
import {LaunchpadSessionLoading} from './LaunchpadSessionLoading';
import {ConfigForRunQuery, ConfigForRunQueryVariables} from './types/ConfigForRunQuery';

export const LaunchpadSetupFromRunRoot: React.FC<{repoAddress: RepoAddress}> = (props) => {
  const {repoAddress} = props;
  const {canLaunchPipelineExecution} = usePermissions();
  const {repoPath, pipelinePath, runId} = useParams<{
    repoPath: string;
    pipelinePath: string;
    runId: string;
  }>();

  if (!canLaunchPipelineExecution.enabled) {
    return <Redirect to={`/workspace/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
  }
  return (
    <LaunchpadSetupFromRunAllowedRoot
      pipelinePath={pipelinePath}
      repoAddress={repoAddress}
      runId={runId}
    />
  );
};

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
  runId: string;
}

/**
 * For a given run ID, retrieve the run config and populate a new Launchpad session with its
 * values, then redirect to the launchpad. The newly created session will be the open launchpad
 * config tab.
 */
const LaunchpadSetupFromRunAllowedRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress, runId} = props;

  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);

  const [storageData, onSave] = useExecutionSessionStorage(repoAddress, pipelineName);

  const {data, loading} = useQuery<ConfigForRunQuery, ConfigForRunQueryVariables>(
    CONFIG_FOR_RUN_QUERY,
    {variables: {runId}},
  );
  const runOrError = data?.runOrError;
  const run = runOrError?.__typename === 'Run' ? runOrError : null;

  React.useEffect(() => {
    // Wait until we have a run, then create the session.
    if (!run) {
      return;
    }

    const {runConfigYaml, mode, solidSelection} = run;
    if (runConfigYaml || mode || solidSelection) {
      // Name the session after this run ID.
      const newSession: Partial<IExecutionSession> = {name: `From run ${run.id.slice(0, 8)}`};

      if (typeof runConfigYaml === 'string') {
        newSession.runConfigYaml = runConfigYaml;
      }
      if (typeof mode === 'string') {
        newSession.mode = mode;
      }
      if (solidSelection instanceof Array && solidSelection.length > 0) {
        newSession.solidSelection = solidSelection as string[];
      } else if (typeof solidSelection === 'string' && solidSelection) {
        newSession.solidSelection = [solidSelection];
      }

      onSave(applyCreateSession(storageData, newSession));
    }
  }, [run, storageData, onSave]);

  if (loading) {
    return <LaunchpadSessionLoading />;
  }

  if (!runOrError || runOrError.__typename === 'RunNotFoundError') {
    return (
      <LaunchpadSessionError
        icon="error"
        title="No run found"
        description="The run with this ID does not exist or has been cleaned up."
      />
    );
  }

  if (runOrError.__typename === 'PythonError') {
    return (
      <LaunchpadSessionError icon="error" title="Python error" description={runOrError.message} />
    );
  }

  return (
    <Redirect
      to={{
        pathname: workspacePathFromAddress(
          repoAddress,
          `/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}/playground`,
        ),
      }}
    />
  );
};

const CONFIG_FOR_RUN_QUERY = gql`
  query ConfigForRunQuery($runId: ID!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        mode
        runConfigYaml
        solidSelection
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
