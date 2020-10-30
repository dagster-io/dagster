import {gql, useQuery} from '@apollo/client';
import {Tag, IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {explorerPathToString, PipelineExplorerPath} from 'src/PipelinePathUtils';
import {TopNav} from 'src/nav/TopNav';
import {FontFamily} from 'src/ui/styles';
import {useActivePipelineForName} from 'src/workspace/WorkspaceContext';

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
  activeTab?: string;
  explorerPath: PipelineExplorerPath;
}

export const SnapshotNav = (props: SnapshotNavProps) => {
  const {activeTab = '', explorerPath} = props;
  const {pipelineName, snapshotId} = explorerPath;
  const explorerPathString = explorerPathToString({
    ...explorerPath,
    pathSolids: [],
  });

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
      href: `/workspace/pipelines/${explorerPath.pipelineName}`,
    },
    {
      text: (
        <div style={{alignItems: 'center', display: 'flex', flexDirection: 'row'}}>
          <Mono>{explorerPath.snapshotId?.slice(0, 8)}</Mono>
          <div style={{width: '70px'}}>{tag()}</div>
        </div>
      ),
    },
  ];

  const tabs = [
    {
      text: 'Definition',
      pathComponent: '',
      href: `/instance/snapshots/${explorerPathString}`,
    },
    {
      text: 'Runs',
      pathComponent: 'runs',
      href: `/instance/snapshots/${explorerPathString}runs`,
    },
  ];

  return (
    <TopNav
      activeTab={tabs.find((tab) => tab.pathComponent === activeTab)?.text}
      breadcrumbs={breadcrumbs}
      tabs={tabs}
    />
  );
};

const Mono = styled.div`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  margin-right: 12px;
`;
