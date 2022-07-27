import {Box, PageHeader, Tabs, Tag, Heading, Tooltip} from '@dagster-io/ui';
import React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {PermissionsMap, PermissionResult, usePermissions} from '../app/Permissions';
import {
  explorerPathFromString,
  explorerPathToString,
  ExplorerPath,
} from '../pipelines/PipelinePathUtils';
import {TabLink} from '../ui/TabLink';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {JobMetadata} from './JobMetadata';
import {RepositoryLink} from './RepositoryLink';

interface TabConfig {
  title: string;
  pathComponent: string;
  getPermissionsResult?: (permissions: PermissionsMap) => PermissionResult;
}

const pipelineTabs: {[key: string]: TabConfig} = {
  overview: {title: 'Overview', pathComponent: ''},
  playground: {
    title: 'Launchpad',
    pathComponent: 'playground',
    getPermissionsResult: (permissions: PermissionsMap) => permissions.canLaunchPipelineExecution,
  },
  runs: {
    title: 'Runs',
    pathComponent: 'runs',
  },
  partitions: {
    title: 'Partitions',
    pathComponent: 'partitions',
  },
};

const currentOrder = ['overview', 'playground', 'runs', 'partitions'];

function tabForPipelinePathComponent(component?: string): TabConfig {
  const tabList = Object.keys(pipelineTabs);
  const match =
    tabList.find((t) => pipelineTabs[t].pathComponent === component) ||
    tabList.find((t) => pipelineTabs[t].pathComponent === '')!;
  return pipelineTabs[match];
}

const tabForKey = (repoAddress: RepoAddress, isJob: boolean, explorerPath: ExplorerPath) => {
  const explorerPathForTab = explorerPathToString({
    ...explorerPath,
    opNames: [],
  });

  // When you click one of the top tabs, it resets the snapshot you may be looking at
  // in the Definition tab and also clears solids from the path
  return (key: string) => {
    const tab = pipelineTabs[key];
    return {
      text: tab.title,
      href: workspacePathFromAddress(
        repoAddress,
        `/${isJob ? 'jobs' : 'pipelines'}/${explorerPathForTab}${tab.pathComponent}`,
      ),
      getPermissionsResult: tab.getPermissionsResult,
    };
  };
};

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineNav: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const permissions = usePermissions();
  const repo = useRepository(repoAddress);
  const match = useRouteMatch<{tab?: string; selector: string}>([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
    '/workspace/:repoPath/jobs/:selector/:tab?',
    '/workspace/:repoPath/pipeline_or_job/:selector/:tab?',
  ]);

  const active = tabForPipelinePathComponent(match!.params.tab);
  const explorerPath = explorerPathFromString(match!.params.selector);
  const {pipelineName, snapshotId} = explorerPath;
  const isJob = isThisThingAJob(repo, pipelineName);
  const partitionSets = repo?.repository.partitionSets || [];

  // If using pipeline:mode tuple (crag flag), check for partition sets that are for this specific
  // pipeline:mode tuple. Otherwise, just check for a pipeline name match.
  const hasPartitionSet = partitionSets.some(
    (partitionSet) => partitionSet.pipelineName === pipelineName,
  );

  const tabs = currentOrder
    .filter((key) => hasPartitionSet || key !== 'partitions')
    .map(tabForKey(repoAddress, isJob, explorerPath));

  return (
    <>
      <PageHeader
        title={<Heading>{pipelineName}</Heading>}
        tags={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 8, wrap: 'wrap'}}>
            <Tag icon="job">
              {isJob ? 'Job in ' : 'Pipeline in '}
              <RepositoryLink repoAddress={repoAddress} />
            </Tag>
            {snapshotId ? null : (
              <JobMetadata pipelineName={pipelineName} repoAddress={repoAddress} />
            )}
          </Box>
        }
        tabs={
          <Tabs size="large" selectedTabId={active.title}>
            {tabs.map((tab) => {
              const {href, text, getPermissionsResult} = tab;
              let permissionsResult = null;
              if (getPermissionsResult) {
                permissionsResult = getPermissionsResult(permissions);
              }
              const disabled = !!(permissionsResult && !permissionsResult.enabled);
              const title =
                permissionsResult && disabled ? (
                  <Tooltip content={permissionsResult.disabledReason} placement="top">
                    {text}
                  </Tooltip>
                ) : (
                  text
                );
              return <TabLink key={text} id={text} title={title} disabled={disabled} to={href} />;
            })}
          </Tabs>
        }
      />
    </>
  );
};
