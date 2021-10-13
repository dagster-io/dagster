import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {explorerPathToString, PipelineExplorerPath} from '../pipelines/PipelinePathUtils';
import {PageHeader} from '../ui/PageHeader';
import {Tab, Tabs} from '../ui/Tabs';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';
import {FontFamily} from '../ui/styles';
import {useActivePipelineForName} from '../workspace/WorkspaceContext';
import {workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {SnapshotQuery} from './types/SnapshotQuery';

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
        <TagWIP intent="none" minimal>
          ...
        </TagWIP>
      );
    }

    if (
      !currentSnapshotID ||
      (currentSnapshotID !== snapshotId &&
        data?.pipelineSnapshotOrError.__typename === 'PipelineSnapshot' &&
        data?.pipelineSnapshotOrError?.parentSnapshotId !== currentSnapshotID)
    ) {
      return (
        <TagWIP intent="warning" minimal>
          Snapshot
        </TagWIP>
      );
    }

    return (
      <TagWIP intent="success" minimal>
        Current
      </TagWIP>
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
          <TagWIP icon="schema">
            Snapshot of{' '}
            <Link
              to={workspacePipelinePathGuessRepo(
                explorerPath.pipelineName,
                explorerPath.pipelineMode,
              )}
            >
              {explorerPath.pipelineName}
            </Link>
          </TagWIP>
          {tag()}
        </>
      }
      tabs={
        <Tabs large={false} selectedTabId={activeTab}>
          {tabs.map((tab) => {
            const {href, text, pathComponent} = tab;
            return <Tab key={text} id={pathComponent} title={text} to={href} />;
          })}
        </Tabs>
      }
    />
  );
};
