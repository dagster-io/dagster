import {buildRepoPath} from './buildRepoAddress';
import {RepoAddress} from './types';

export const workspacePath = (repoName: string, repoLocation: string, path = '') => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${buildRepoPath(repoName, repoLocation)}${finalPath}`;
};

type PathConfig = {
  repoName: string;
  repoLocation: string;
  pipelineName: string;
  isJob: boolean;
  path?: string;
};

export const workspacePipelinePath = ({
  repoName,
  repoLocation,
  pipelineName,
  isJob,
  path = '',
}: PathConfig) => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${buildRepoPath(repoName, repoLocation)}/${
    isJob ? 'jobs' : 'pipelines'
  }/${pipelineName}${finalPath}`;
};

export const workspacePipelinePathGuessRepo = (pipelineName: string, isJob = false, path = '') => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/workspace/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}${finalPath}`;
};

export const workspacePathFromAddress = (repoAddress: RepoAddress, path = '') => {
  const {name, location} = repoAddress;
  return workspacePath(name, location, path);
};

type RunDetails = {
  id: string;
  pipelineName: string;
  repositoryName?: string;
  repositoryLocationName?: string;
  isJob: boolean;
};

export const workspacePathFromRunDetails = ({
  id,
  pipelineName,
  repositoryName,
  repositoryLocationName,
  isJob,
}: RunDetails) => {
  const path = `/playground/setup-from-run/${id}`;

  if (repositoryName != null && repositoryLocationName != null) {
    return workspacePipelinePath({
      repoName: repositoryName,
      repoLocation: repositoryLocationName,
      pipelineName,
      isJob,
      path,
    });
  }

  return workspacePipelinePathGuessRepo(pipelineName, isJob, path);
};
