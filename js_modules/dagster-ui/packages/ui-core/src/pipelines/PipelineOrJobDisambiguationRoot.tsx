import {useContext} from 'react';
import {Redirect, useLocation, useParams} from 'react-router-dom';

import {explorerPathFromString} from './PipelinePathUtils';
import {PermissionsContext} from '../app/Permissions';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineOrJobDisambiguationRoot = (props: Props) => {
  const {repoAddress} = props;
  const location = useLocation();
  const {pipelinePath} = useParams<{pipelinePath: string}>();

  const {loading} = useContext(WorkspaceContext);
  const {loading: permissionsLoading} = useContext(PermissionsContext);
  const repo = useRepository(repoAddress);

  useBlockTraceUntilTrue('Workspace', loading);
  useBlockTraceUntilTrue('Permissions', permissionsLoading);
  if (loading || permissionsLoading) {
    return null;
  }

  const {pipelineName: pipelineOrJobName} = explorerPathFromString(pipelinePath);
  const isJob = isThisThingAJob(repo, pipelineOrJobName);
  const {pathname, search} = location;

  const replacedPath = pathname.replace('/pipeline_or_job/', isJob ? '/jobs/' : '/pipelines/');

  return <Redirect to={`${replacedPath}${search}`} />;
};
