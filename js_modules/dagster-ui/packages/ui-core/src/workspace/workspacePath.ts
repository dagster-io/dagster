import {IconName} from '@dagster-io/ui-components';
import {NO_LAUNCH_PERMISSION_MESSAGE} from 'shared/launchpad/LaunchRootExecutionButton.oss';

import {buildRepoPathForURL} from './buildRepoAddress';
import {RepoAddress} from './types';
import {isHiddenAssetGroupJob, tokenForAssetKey} from '../asset-graph/Utils';
import {globalAssetGraphPathToString} from '../assets/globalAssetGraphPathToString';
import {AssetKey} from '../graphql/types';
import {isExternalRun} from '../runs/externalRuns';

export const workspacePath = (repoName: string, repoLocation: string, path = '') => {
  const finalPath = path.startsWith('/') ? path : `/${path}`;
  return `/locations/${buildRepoPathForURL(repoName, repoLocation)}${finalPath}`;
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
  const finalPath = path === '' ? '' : path.startsWith('/') ? path : `/${path}`;
  return `/locations/${buildRepoPathForURL(repoName, repoLocation)}/${
    isJob ? 'jobs' : 'pipelines'
  }/${pipelineName}${finalPath}`;
};

export const workspacePipelinePathGuessRepo = (pipelineName: string, path = '') => {
  const finalPath = path === '' ? '' : path.startsWith('/') ? path : `/${path}`;
  return `/guess/${pipelineName}${finalPath}`;
};

export const workspacePathFromAddress = (repoAddress: RepoAddress, path = '') => {
  const {name, location} = repoAddress;
  return workspacePath(name, location, path);
};

type RunDetails = {
  run: {
    id: string;
    pipelineName: string;
    executionPlan?: null | {assetKeys: AssetKey[]};
    assetCheckSelection:
      | null
      | {
          name: string;
          assetKey: AssetKey;
        }[];
    tags: {
      key: string;
      value: string;
    }[];
    hasReExecutePermission: boolean;
  };
  repositoryName?: string;
  repositoryLocationName?: string;
  isJob: boolean;
};

/**
 * Returns a link path, label, and disabled reason for linking to the run belonging to a job.
 * For asset jobs, this may be a link to the asset graph if the job is hidden. For asset
 * jobs, it will be a link to the job page, and for op jobs a link to the job launchpad.
 */
export const workspacePipelineLinkForRun = ({
  run,
  repositoryName,
  repositoryLocationName,
  isJob,
}: RunDetails) => {
  if (isHiddenAssetGroupJob(run.pipelineName)) {
    const keys = run.executionPlan?.assetKeys ?? [];
    const opsQuery = keys.map((key) => `key:"${tokenForAssetKey(key)}"`).join(' or ');

    return {
      disabledReason: null,
      label: `View asset lineage`,
      icon: 'lineage' as IconName,
      to: globalAssetGraphPathToString({opsQuery, opNames: []}),
    };
  }

  const isAssetJob = run.assetCheckSelection?.length || run.executionPlan?.assetKeys?.length;
  const isExternalJob = isExternalRun(run);
  const path = isAssetJob || isExternalJob ? '/' : `/playground/setup-from-run/${run.id}`;
  const to =
    repositoryName != null && repositoryLocationName != null
      ? workspacePipelinePath({
          repoName: repositoryName,
          repoLocation: repositoryLocationName,
          pipelineName: run.pipelineName,
          isJob,
          path,
        })
      : workspacePipelinePathGuessRepo(run.pipelineName, path);

  return {
    to,
    label: isAssetJob || isExternalJob ? 'View job' : 'Open in Launchpad',
    icon: isAssetJob || isExternalJob ? ('job' as IconName) : ('edit' as IconName),
    disabledReason: isAssetJob || run.hasReExecutePermission ? null : NO_LAUNCH_PERMISSION_MESSAGE,
  };
};
