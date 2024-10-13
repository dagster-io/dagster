import qs from 'qs';
import {useEffect} from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {
  IExecutionSession,
  applyCreateSession,
  useExecutionSessionStorage,
} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const LaunchpadSetupRoot = (props: {repoAddress: RepoAddress}) => {
  const {repoAddress} = props;
  const {
    permissions: {canLaunchPipelineExecution},
    loading,
  } = usePermissionsForLocation(repoAddress.location);

  useBlockTraceUntilTrue('Permissions', loading);

  const {repoPath, pipelinePath} = useParams<{repoPath: string; pipelinePath: string}>();
  if (loading) {
    return null;
  }

  if (!canLaunchPipelineExecution) {
    return <Redirect to={`/locations/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
  }
  return <LaunchpadSetupAllowedRoot pipelinePath={pipelinePath} repoAddress={repoAddress} />;
};

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

const LaunchpadSetupAllowedRoot = (props: Props) => {
  const {pipelinePath, repoAddress} = props;

  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);

  const [_, onSave] = useExecutionSessionStorage(repoAddress, pipelineName);
  const queryString = qs.parse(window.location.search, {ignoreQueryPrefix: true});

  useEffect(() => {
    if (
      queryString.config ||
      queryString.mode ||
      queryString.solidSelection ||
      queryString.tags ||
      queryString.assetSelection
    ) {
      const newSession: Partial<IExecutionSession> = {};
      if (typeof queryString.config === 'string') {
        newSession.runConfigYaml = queryString.config;
      }
      if (typeof queryString.mode === 'string') {
        newSession.mode = queryString.mode;
      }
      if (queryString.solidSelection instanceof Array && queryString.solidSelection.length > 0) {
        newSession.solidSelection = queryString.solidSelection as string[];
      } else if (typeof queryString.solidSelection === 'string' && queryString.solidSelection) {
        newSession.solidSelection = [queryString.solidSelection];
      }
      if (typeof queryString.solidSelectionQuery === 'string') {
        newSession.solidSelectionQuery = queryString.solidSelectionQuery;
      }

      if (Array.isArray(queryString.tags)) {
        newSession.tags = queryString.tags as any;
      }

      if (Array.isArray(queryString.assetSelection)) {
        newSession.assetSelection = queryString.assetSelection as any;
      }

      onSave((data) => applyCreateSession(data, newSession));
    }
  });

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
