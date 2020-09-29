import {IBreadcrumbProps, Tag} from '@blueprintjs/core';
import React from 'react';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components';

import {useRepository} from 'src/DagsterRepositoryContext';
import {explorerPathFromString, explorerPathToString} from 'src/PipelinePathUtils';
import {TopNav} from 'src/nav/TopNav';

const pipelineTabs = {
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

export function tabForPipelinePathComponent(component?: string) {
  const tabList = Object.keys(pipelineTabs);
  const match =
    tabList.find((t) => pipelineTabs[t].pathComponent === component) ||
    tabList.find((t) => pipelineTabs[t].pathComponent === '')!;
  return pipelineTabs[match];
}

interface PipelineNavProps {
  isHistorical: boolean;
  isSnapshot: boolean;
}

export const PipelineNav: React.FunctionComponent<PipelineNavProps> = (props: PipelineNavProps) => {
  const {isHistorical, isSnapshot} = props;
  const repository = useRepository();
  const match = useRouteMatch<{tab: string; selector: string}>(['/pipeline/:selector/:tab?']);

  const active = tabForPipelinePathComponent(match.params.tab);
  const explorerPath = explorerPathFromString(match.params.selector);
  const hasPartitionSet = repository?.partitionSets
    .map((x) => x.pipelineName)
    .includes(explorerPath.pipelineName);

  // When you click one of the top tabs, it resets the snapshot you may be looking at
  // in the Definition tab and also clears solids from the path
  const explorerPathForTab = explorerPathToString({
    ...explorerPath,
    pathSolids: [],
  });

  const breadcrumbs: IBreadcrumbProps[] = [{text: 'Pipelines', icon: 'diagram-tree'}];

  if (isSnapshot) {
    const tag = isHistorical ? (
      <Tag intent="warning" minimal>
        Historical snapshot
      </Tag>
    ) : (
      <Tag intent="success" minimal>
        Current snapshot
      </Tag>
    );

    breadcrumbs.push(
      {
        text: explorerPath.pipelineName,
        href: `/pipeline/${explorerPath.pipelineName}`,
      },
      {
        text: (
          <div style={{alignItems: 'center', display: 'flex', flexDirection: 'row'}}>
            <Mono>{explorerPath.snapshotId}</Mono>
            {tag}
          </div>
        ),
      },
    );
  } else {
    breadcrumbs.push({
      text: explorerPath.pipelineName,
    });
  }

  const tabForKey = React.useCallback(
    (key) => {
      const tab = pipelineTabs[key];
      return {
        text: tab.title,
        href: `/pipeline/${explorerPathForTab}${tab.pathComponent}`,
      };
    },
    [explorerPathForTab],
  );

  const tabs = React.useMemo(() => {
    return isSnapshot
      ? snapshotOrder.map(tabForKey)
      : currentOrder.filter((key) => hasPartitionSet || key !== 'partitions').map(tabForKey);
  }, [hasPartitionSet, isSnapshot, tabForKey]);

  return <TopNav activeTab={active.title} breadcrumbs={breadcrumbs} tabs={tabs} />;
};

const Mono = styled.div`
  font-family: monospace;
  font-size: 14px;
  margin-right: 12px;
`;
