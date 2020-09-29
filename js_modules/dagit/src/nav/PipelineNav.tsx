import {IBreadcrumbProps, IconName} from '@blueprintjs/core';
import React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {useRepository} from 'src/DagsterRepositoryContext';
import {explorerPathFromString, explorerPathToString} from 'src/PipelinePathUtils';
import {TopNav} from 'src/nav/TopNav';

const PIPELINE_TABS: {
  title: string;
  pathComponent: string;
  icon: IconName;
}[] = [
  {title: 'Overview', pathComponent: 'overview', icon: 'dashboard'},
  {title: 'Definition', pathComponent: '', icon: 'diagram-tree'},
  {
    title: 'Playground',
    pathComponent: 'playground',
    icon: 'manually-entered-data',
  },
  {
    title: 'Runs',
    pathComponent: 'runs',
    icon: 'history',
  },
  {
    title: 'Partitions',
    pathComponent: 'partitions',
    icon: 'multi-select',
  },
];

export function tabForPipelinePathComponent(component?: string) {
  return (
    PIPELINE_TABS.find((t) => t.pathComponent === component) ||
    PIPELINE_TABS.find((t) => t.pathComponent === '')!
  );
}

export const PipelineNav: React.FunctionComponent = () => {
  const repository = useRepository();
  const match = useRouteMatch<{tab: string; selector: string}>(['/pipeline/:selector/:tab?']);
  if (!match) {
    return <span />;
  }

  const active = tabForPipelinePathComponent(match.params.tab);
  const explorerPath = explorerPathFromString(match.params.selector);
  const hasPartitionSet = repository?.partitionSets
    .map((x) => x.pipelineName)
    .includes(explorerPath.pipelineName);

  // When you click one of the top tabs, it resets the snapshot you may be looking at
  // in the Definition tab and also clears solids from the path
  const explorerPathWithoutSnapshot = explorerPathToString({
    ...explorerPath,
    snapshotId: undefined,
    pathSolids: [],
  });

  const breadcrumbs: IBreadcrumbProps[] = [
    {text: 'Pipelines', icon: 'diagram-tree'},
    {text: explorerPath.pipelineName},
  ];

  const tabs = PIPELINE_TABS.filter(
    (tab) => hasPartitionSet || tab.pathComponent !== 'partitions',
  ).map((tab) => {
    return {
      text: tab.title,
      href: `/pipeline/${explorerPathWithoutSnapshot}${tab.pathComponent}`,
    };
  });

  return <TopNav activeTab={active.title} breadcrumbs={breadcrumbs} tabs={tabs} />;
};
