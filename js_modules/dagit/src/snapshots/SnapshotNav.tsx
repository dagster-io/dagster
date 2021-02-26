import {gql, useQuery} from '@apollo/client';
import {Tag, Colors, Tab, Tabs} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {explorerPathToString, PipelineExplorerPath} from 'src/pipelines/PipelinePathUtils';
import {SnapshotQuery} from 'src/snapshots/types/SnapshotQuery';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';
import {FontFamily} from 'src/ui/styles';
import {useActivePipelineForName} from 'src/workspace/WorkspaceContext';

const SNAPSHOT_PARENT_QUERY = gql`
  query SnapshotQuery($snapshotId: String!) {
    pipelineSnapshotOrError(snapshotId: $snapshotId) {
      ... on PipelineSnapshot {
        id
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

  const {data, loading} = useQuery<SnapshotQuery>(SNAPSHOT_PARENT_QUERY, {
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
        data?.pipelineSnapshotOrError.__typename === 'PipelineSnapshot' &&
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
    <Group direction="column" spacing={12} padding={{top: 20, horizontal: 20}}>
      <PageHeader
        title={
          <Group direction="row" spacing={12} alignItems="flex-end">
            <Heading style={{fontFamily: FontFamily.monospace}}>
              {explorerPath.snapshotId?.slice(0, 8)}
            </Heading>
            {tag()}
          </Group>
        }
        icon="diagram-tree"
        description={
          <span>
            Snapshot of{' '}
            <Link to={`/workspace/pipelines/${explorerPath.pipelineName}`}>
              {explorerPath.pipelineName}
            </Link>
          </span>
        }
      />
      <Box border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}>
        <Tabs large={false} selectedTabId={activeTab}>
          {tabs.map((tab) => {
            const {href, text, pathComponent} = tab;
            return <Tab key={text} id={pathComponent} title={<Link to={href}>{text}</Link>} />;
          })}
        </Tabs>
      </Box>
    </Group>
  );
};
