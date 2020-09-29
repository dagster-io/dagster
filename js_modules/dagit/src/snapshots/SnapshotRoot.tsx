import {IBreadcrumbProps, NonIdealState, Tag} from '@blueprintjs/core';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Loading} from 'src/Loading';
import {PIPELINE_EXPLORER_ROOT_QUERY} from 'src/PipelineExplorerRoot';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {TopNav} from 'src/nav/TopNav';
import {
  PipelineExplorerRootQuery,
  PipelineExplorerRootQueryVariables,
} from 'src/types/PipelineExplorerRootQuery';

export const SnapshotRoot: React.FunctionComponent<any> = (props) => {
  const {params} = props.match;
  const {pipelinePath} = params;
  const {pipelineName, snapshotId} = explorerPathFromString(pipelinePath);

  const queryResult = useQuery<PipelineExplorerRootQuery, PipelineExplorerRootQueryVariables>(
    PIPELINE_EXPLORER_ROOT_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {
        snapshotId,
        rootHandleID: '',
      },
    },
  );

  return (
    <div style={{display: 'flex', flexDirection: 'column', width: '100%'}}>
      <Loading queryResult={queryResult}>
        {(data) => {
          const snapshotData = data?.pipelineSnapshotOrError;

          if (snapshotData.__typename === 'PipelineSnapshotNotFoundError') {
            const {message} = snapshotData;
            return <NonIdealState icon="camera" title="Snapshot not found" description={message} />;
          }

          const pipelineForSnapshot =
            snapshotData?.__typename === 'PipelineSnapshot' ? snapshotData?.name : null;

          if (
            snapshotData.__typename === 'PipelineSnapshot' &&
            pipelineName !== pipelineForSnapshot
          ) {
            return (
              <NonIdealState
                icon="camera"
                title="Snapshot not found"
                description={`Snapshot ${snapshotId} could not be found for pipeline ${pipelineName}`}
              />
            );
          }

          const items: IBreadcrumbProps[] = [
            {icon: 'diagram-tree', text: 'Pipelines'},
            {text: pipelineName, href: `/pipeline/${pipelineName}`},
            {
              text: (
                <div style={{alignItems: 'center', display: 'flex', flexDirection: 'row'}}>
                  <Mono>{snapshotId}</Mono>
                  <Tag intent="warning" minimal>
                    Historical snapshot
                  </Tag>
                </div>
              ),
            },
          ];

          const tabs = [
            {
              text: 'Definition',
              href: `/snapshot/${pipelinePath}/definition`,
            },
            {
              text: 'Runs',
              href: `/snapshot/${pipelinePath}/runs`,
            },
          ];

          return (
            <>
              <TopNav breadcrumbs={items} tabs={tabs} />
              <div style={{flexGrow: 1, padding: '16px'}}>
                {pipelineName ? (
                  <div>
                    Pipeline: <Link to={`/pipeline/${pipelineName}`}>{pipelineName}</Link>
                  </div>
                ) : null}
              </div>
            </>
          );
        }}
      </Loading>
    </div>
  );
};

const Mono = styled.div`
  font-family: monospace;
  font-size: 16px;
  margin-right: 12px;
`;
