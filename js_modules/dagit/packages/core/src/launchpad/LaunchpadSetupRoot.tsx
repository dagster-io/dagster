import qs from 'qs';
import * as React from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {
  IExecutionSession,
  applyCreateSession,
  useExecutionSessionStorage,
} from '../app/ExecutionSessionStorage';
import {usePermissions} from '../app/Permissions';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const LaunchpadSetupRoot: React.FC<{repoAddress: RepoAddress}> = (props) => {
  const {repoAddress} = props;
  const {canLaunchPipelineExecution} = usePermissions();
  const {repoPath, pipelinePath} = useParams<{repoPath: string; pipelinePath: string}>();

  if (!canLaunchPipelineExecution.enabled) {
    return <Redirect to={`/workspace/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
  }
  return <LaunchpadSetupAllowedRoot pipelinePath={pipelinePath} repoAddress={repoAddress} />;
};

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

const LaunchpadSetupAllowedRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;

  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);

  const [data, onSave] = useExecutionSessionStorage(repoAddress, pipelineName);
  const queryString = qs.parse(window.location.search, {ignoreQueryPrefix: true});

  React.useEffect(() => {
    if (queryString.config || queryString.mode || queryString.solidSelection) {
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

      onSave(applyCreateSession(data, newSession));
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
