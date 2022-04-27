import {gql, useQuery} from '@apollo/client';
import {PageHeader, Tabs, Tag, Heading, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {explorerPathToString, ExplorerPath} from '../pipelines/PipelinePathUtils';
import {TabLink} from '../ui/TabLink';
import {useActivePipelineForName} from '../workspace/WorkspaceContext';
import {workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {SnapshotQuery, SnapshotQueryVariables} from './types/SnapshotQuery';

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
  explorerPath: ExplorerPath;
}

export const SnapshotNav = (props: SnapshotNavProps) => {
  const {activeTab = '', explorerPath} = props;
  const {pipelineName, snapshotId = ''} = explorerPath;
  const explorerPathString = explorerPathToString({
    ...explorerPath,
    opNames: [],
  });

  const currentPipelineState = useActivePipelineForName(pipelineName);
  const isJob = !!currentPipelineState?.isJob;
  const currentSnapshotID = currentPipelineState?.pipelineSnapshotId;

  const {data, loading} = useQuery<SnapshotQuery, SnapshotQueryVariables>(SNAPSHOT_PARENT_QUERY, {
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
    <PageHeader
      title={
        <Heading style={{fontFamily: FontFamily.monospace, fontSize: '20px'}}>
          {explorerPath.snapshotId?.slice(0, 8)}
        </Heading>
      }
      tags={
        <>
          <Tag icon="schema">
            Snapshot of{' '}
            <Link to={workspacePipelinePathGuessRepo(explorerPath.pipelineName, isJob)}>
              {explorerPath.pipelineName}
            </Link>
          </Tag>
          {tag()}
        </>
      }
      tabs={
        <Tabs selectedTabId={activeTab}>
          {tabs.map((tab) => {
            const {href, text, pathComponent} = tab;
            return <TabLink key={text} id={pathComponent} title={text} to={href} />;
          })}
        </Tabs>
      }
    />
  );
};
