import {buildRepoPath} from './buildRepoAddress';
import {RepoAddress} from './types';

export const workspacePath = (repoName: string, repoLocation: string, path = '') => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${buildRepoPath(repoName, repoLocation)}${finalPath}`;
};

export const workspacePipelinePath = (
  repoName: string,
  repoLocation: string,
  pipelineName: string,
  pipelineMode: string,
  path = '',
) => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${buildRepoPath(
    repoName,
    repoLocation,
  )}/pipelines/${pipelineName}:${pipelineMode}${finalPath}`;
};

export const workspacePipelinePathGuessRepo = (
  pipelineName: string,
  pipelineMode: string,
  path = '',
) => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/pipelines/${pipelineName}:${pipelineMode}${finalPath}`;
};

export const workspacePathFromAddress = (repoAddress: RepoAddress, path = '') => {
  const {name, location} = repoAddress;
  return workspacePath(name, location, path);
};
