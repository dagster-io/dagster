import {FontFamily, PageHeader, Subtitle1, Tabs, Tag} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import {SnapshotQuery, SnapshotQueryVariables} from './types/SnapshotNav.types';
import {ExplorerPath, explorerPathToString} from '../pipelines/PipelinePathUtils';
import {TabLink} from '../ui/TabLink';
import {useActivePipelineForName} from '../workspace/WorkspaceContext/util';
import {workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

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
  const currentSnapshotID = currentPipelineState?.pipelineSnapshotId;

  const queryResult = useQuery<SnapshotQuery, SnapshotQueryVariables>(SNAPSHOT_PARENT_QUERY, {
    variables: {snapshotId},
  });

  const {data, loading} = queryResult;

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
      href: `/snapshots/${explorerPathString}`,
    },
    {
      text: 'Runs',
      pathComponent: 'runs',
      href: `/snapshots/${explorerPathString}runs`,
    },
  ];

  return (
    <PageHeader
      title={
        <Subtitle1 style={{fontFamily: FontFamily.monospace, fontSize: '16px'}}>
          {explorerPath.snapshotId?.slice(0, 8)}
        </Subtitle1>
      }
      tags={
        <>
          <Tag icon="schema">
            Snapshot of{' '}
            <Link to={workspacePipelinePathGuessRepo(explorerPath.pipelineName)}>
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
