import {IBreadcrumbProps, IconName} from '@blueprintjs/core';
import React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {
  explorerPathFromString,
  explorerPathToString,
  PipelineExplorerPath,
} from 'src/PipelinePathUtils';
import {TopNav} from 'src/nav/TopNav';
import {useWorkspaceState} from 'src/workspace/WorkspaceContext';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Tab {
  title: string;
  pathComponent: string;
  icon: IconName;
}

const pipelineTabs: {[key: string]: Tab} = {
  overview: {title: 'Overview', pathComponent: 'overview', icon: 'dashboard'},
  definition: {title: 'Definition', pathComponent: '', icon: 'diagram-tree'},
  playground: {
    title: 'Playground',
    pathComponent: 'playground',
    icon: 'manually-entered-data',
  },
  runs: {
    title: 'Runs',
    pathComponent: 'runs',
    icon: 'history',
  },
  partitions: {
    title: 'Partitions',
    pathComponent: 'partitions',
    icon: 'multi-select',
  },
};

const currentOrder = ['overview', 'definition', 'playground', 'runs', 'partitions'];

export function tabForPipelinePathComponent(component?: string): Tab {
  const tabList = Object.keys(pipelineTabs);
  const match =
    tabList.find((t) => pipelineTabs[t].pathComponent === component) ||
    tabList.find((t) => pipelineTabs[t].pathComponent === '')!;
  return pipelineTabs[match];
}

const tabForKey = (repoAddress: RepoAddress, explorerPath: PipelineExplorerPath) => {
  const explorerPathForTab = explorerPathToString({
    ...explorerPath,
    pathSolids: [],
  });

  // When you click one of the top tabs, it resets the snapshot you may be looking at
  // in the Definition tab and also clears solids from the path
  return (key: string) => {
    const tab = pipelineTabs[key];
    return {
      text: tab.title,
      href: workspacePathFromAddress(
        repoAddress,
        `/pipelines/${explorerPathForTab}${tab.pathComponent}`,
      ),
    };
  };
};

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineNav: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const {activeRepo} = useWorkspaceState();
  const match = useRouteMatch<{tab: string; selector: string}>([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
  ]);

  const active = tabForPipelinePathComponent(match.params.tab);
  const explorerPath = explorerPathFromString(match.params.selector);

  const hasPartitionSet = activeRepo?.repo.repository.partitionSets
    .map((x) => x.pipelineName)
    .includes(explorerPath.pipelineName);

  const breadcrumbs: IBreadcrumbProps[] = [
    {text: 'Pipelines', icon: 'diagram-tree'},
    {text: explorerPath.pipelineName},
  ];

  const tabs = currentOrder
    .filter((key) => hasPartitionSet || key !== 'partitions')
    .map(tabForKey(repoAddress, explorerPath));

  return <TopNav activeTab={active.title} breadcrumbs={breadcrumbs} tabs={tabs} />;
};
