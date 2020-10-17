import {IBreadcrumbProps, IconName, Tag} from '@blueprintjs/core';
import gql from 'graphql-tag';
import React from 'react';
import {useQuery} from 'react-apollo';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components';

import {useActivePipelineForName, useRepository} from 'src/DagsterRepositoryContext';
import {
  explorerPathFromString,
  explorerPathToString,
  PipelineExplorerPath,
} from 'src/PipelinePathUtils';
import {TopNav} from 'src/nav/TopNav';
import {FontFamily} from 'src/ui/styles';

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

const snapshotOrder = ['definition', 'runs'];
const currentOrder = ['overview', 'definition', 'playground', 'runs', 'partitions'];

export function tabForPipelinePathComponent(component?: string): Tab {
  const tabList = Object.keys(pipelineTabs);
  const match =
    tabList.find((t) => pipelineTabs[t].pathComponent === component) ||
    tabList.find((t) => pipelineTabs[t].pathComponent === '')!;
  return pipelineTabs[match];
}

const tabForKey = (explorerPath: PipelineExplorerPath) => {
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
      href: `/pipeline/${explorerPathForTab}${tab.pathComponent}`,
    };
  };
};

const SNAPSHOT_PARENT_QUERY = gql`
  query SnapshotQuery($snapshotId: String!) {
    pipelineSnapshotOrError(snapshotId: $snapshotId) {
      ... on PipelineSnapshot {
        parentSnapshotId
      }
    }
  }
`;

interface SnapshotNavProps {
  active: Tab;
  explorerPath: PipelineExplorerPath;
}

const SnapshotNav = (props: SnapshotNavProps) => {
  const {active, explorerPath} = props;
  const {pipelineName, snapshotId} = explorerPath;

  const currentPipelineState = useActivePipelineForName(pipelineName);
  const currentSnapshotID = currentPipelineState?.pipelineSnapshotId;

  const {data, loading} = useQuery(SNAPSHOT_PARENT_QUERY, {
    variables: {snapshotId},
  });

  const tag = () => {
    if (loading) {
      return (
        <Tag intent="none" minimal>
          ...
        </Tag>
      );
    }

    if (
      !currentSnapshotID ||
      (currentSnapshotID !== snapshotId &&
        data?.pipelineSnapshotOrError?.parentSnapshotId !== currentSnapshotID)
    ) {
      return (
        <Tag intent="warning" minimal>
          Snapshot
        </Tag>
      );
    }

    return (
      <Tag intent="success" minimal>
        Current
      </Tag>
    );
  };

  const breadcrumbs: IBreadcrumbProps[] = [
    {text: 'Pipelines', icon: 'diagram-tree'},
    {
      text: explorerPath.pipelineName,
      href: `/pipeline/${explorerPath.pipelineName}`,
    },
    {
      text: (
        <div style={{alignItems: 'center', display: 'flex', flexDirection: 'row'}}>
          <Mono>{explorerPath.snapshotId}</Mono>
          <div style={{width: '70px'}}>{tag()}</div>
        </div>
      ),
    },
  ];

  const tabs = snapshotOrder.map(tabForKey(explorerPath));
  return <TopNav activeTab={active.title} breadcrumbs={breadcrumbs} tabs={tabs} />;
};

interface CurrentPipelineNavProps {
  active: Tab;
  explorerPath: PipelineExplorerPath;
}

const CurrentPipelineNav = (props: CurrentPipelineNavProps) => {
  const {active, explorerPath} = props;
  const repository = useRepository();

  const hasPartitionSet = repository?.partitionSets
    .map((x) => x.pipelineName)
    .includes(explorerPath.pipelineName);

  const breadcrumbs: IBreadcrumbProps[] = [
    {text: 'Pipelines', icon: 'diagram-tree'},
    {text: explorerPath.pipelineName},
  ];

  const tabs = currentOrder
    .filter((key) => hasPartitionSet || key !== 'partitions')
    .map(tabForKey(explorerPath));

  return <TopNav activeTab={active.title} breadcrumbs={breadcrumbs} tabs={tabs} />;
};

export const PipelineNav: React.FunctionComponent<{}> = () => {
  const match = useRouteMatch<{tab: string; selector: string}>(['/pipeline/:selector/:tab?']);
  const active = tabForPipelinePathComponent(match.params.tab);
  const explorerPath = explorerPathFromString(match.params.selector);
  const {snapshotId} = explorerPath;

  if (snapshotId) {
    return <SnapshotNav active={active} explorerPath={explorerPath} />;
  }
  return <CurrentPipelineNav active={active} explorerPath={explorerPath} />;
};

const Mono = styled.div`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  margin-right: 12px;
`;
