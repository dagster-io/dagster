import {IconName, Tab, Tabs, Colors} from '@blueprintjs/core';
import React from 'react';
import {Link, useRouteMatch} from 'react-router-dom';

import {
  explorerPathFromString,
  explorerPathToString,
  PipelineExplorerPath,
} from 'src/pipelines/PipelinePathUtils';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';
import {useRepository} from 'src/workspace/WorkspaceContext';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface TabConfig {
  title: string;
  pathComponent: string;
  icon: IconName;
}

const pipelineTabs: {[key: string]: TabConfig} = {
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

export function tabForPipelinePathComponent(component?: string): TabConfig {
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
  const repo = useRepository(repoAddress);
  const match = useRouteMatch<{tab?: string; selector: string}>([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
  ]);

  const active = tabForPipelinePathComponent(match!.params.tab);
  const explorerPath = explorerPathFromString(match!.params.selector);

  const hasPartitionSet = repo?.repository.partitionSets
    .map((x) => x.pipelineName)
    .includes(explorerPath.pipelineName);

  const tabs = currentOrder
    .filter((key) => hasPartitionSet || key !== 'partitions')
    .map(tabForKey(repoAddress, explorerPath));

  return (
    <Group direction="column" spacing={12} padding={{top: 20, horizontal: 20}}>
      <PageHeader
        title={<Heading>{explorerPath.pipelineName}</Heading>}
        icon="diagram-tree"
        description={
          <>
            <Link to={workspacePathFromAddress(repoAddress, '/pipelines')}>Pipeline</Link> in{' '}
            <Link to={workspacePathFromAddress(repoAddress)}>
              {repoAddressAsString(repoAddress)}
            </Link>
          </>
        }
      />
      <Box border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Tabs large={false} selectedTabId={active.title}>
          {tabs.map((tab) => {
            const {href, text} = tab;
            return <Tab key={text} id={text} title={<Link to={href}>{text}</Link>} />;
          })}
        </Tabs>
      </Box>
    </Group>
  );
};
