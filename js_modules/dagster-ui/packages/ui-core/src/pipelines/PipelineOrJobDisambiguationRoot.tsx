import * as React from 'react';
import {Redirect, useLocation, useParams} from 'react-router-dom';

import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {explorerPathFromString} from './PipelinePathUtils';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineOrJobDisambiguationRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const location = useLocation();
  const {pipelinePath} = useParams<{pipelinePath: string}>();

  const {pipelineName: pipelineOrJobName} = explorerPathFromString(pipelinePath);
  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineOrJobName);
  const {pathname, search} = location;

  const replacedPath = pathname.replace('/pipeline_or_job/', isJob ? '/jobs/' : '/pipelines/');

  return <Redirect to={`${replacedPath}${search}`} />;
};
