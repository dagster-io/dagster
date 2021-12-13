import * as React from 'react';
import {Redirect, RouteComponentProps, useLocation} from 'react-router-dom';

import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {explorerPathFromString} from './PipelinePathUtils';

interface Props extends RouteComponentProps<{repoPath: string; pipelinePath: string}> {
  repoAddress: RepoAddress;
}

export const PipelineOrJobDisambiguationRoot: React.FC<Props> = (props) => {
  const location = useLocation();
  const {repoAddress} = props;
  const {pipelinePath} = props.match.params;
  const {pipelineName: pipelineOrJobName} = explorerPathFromString(pipelinePath);
  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineOrJobName);
  const {search} = location;

  const replacedPath = props.match.url.replace(
    '/pipeline_or_job/',
    isJob ? '/jobs/' : '/pipelines/',
  );

  return <Redirect to={`${replacedPath}${search}`} />;
};
