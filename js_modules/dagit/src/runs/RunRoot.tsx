import {gql, useApolloClient, useQuery} from '@apollo/client';
import {IBreadcrumbProps, NonIdealState, Spinner} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetsSupported} from 'src/AssetsSupported';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {Run} from 'src/runs/Run';
import {RunFragments} from 'src/runs/RunFragments';
import {RunStatusTag} from 'src/runs/RunStatusTag';
import {RunRootQuery} from 'src/runs/types/RunRootQuery';
import {FontFamily} from 'src/ui/styles';

export const RunRoot: React.FC<RouteComponentProps<{runId: string}>> = (props) => {
  const runId = props.match.params.runId;

  const {data, loading, error} = useQuery<RunRootQuery>(RUN_ROOT_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    variables: {runId},
  });

  const run =
    data?.pipelineRunOrError.__typename === 'PipelineRun' ? data.pipelineRunOrError : null;

  const lastBreadcrumb = () => {
    if (loading) {
      return <Spinner size={12} />;
    }
    if (error || !run) {
      return <Mono>{runId}</Mono>;
    }
    return (
      <div
        style={{display: 'flex', flexDirection: 'row', alignItems: 'center', fontWeight: 'normal'}}
      >
        <Link to={`/instance/snapshots/${run.pipeline.name}@${run.pipelineSnapshotId}`}>
          {run.pipeline.name}
        </Link>
        <div style={{margin: '0 8px'}}>:</div>
        <Mono>Run {runId.slice(0, 8)}</Mono>
        <div style={{marginLeft: '12px'}}>
          <RunStatusTag status={run.status} />
        </div>
      </div>
    );
  };

  const breadcrumbs: IBreadcrumbProps[] = [
    {text: 'Runs', icon: 'history', href: '/instance/runs'},
    {text: lastBreadcrumb()},
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
        width: '100%',
        height: '100%',
      }}
    >
      <TopNav breadcrumbs={breadcrumbs} />
      <RunById data={data} runId={runId} />
    </div>
  );
};

export const RunById: React.FC<{data: RunRootQuery | undefined; runId: string}> = (props) => {
  const {data, runId} = props;
  useDocumentTitle(`Run: ${runId}`);

  const client = useApolloClient();

  if (!data || !data.pipelineRunOrError) {
    return <Run client={client} run={undefined} runId={runId} />;
  }

  if (data.pipelineRunOrError.__typename !== 'PipelineRun') {
    return (
      <NonIdealState
        icon={IconNames.SEND_TO_GRAPH}
        title="No Run"
        description={'The run with this ID does not exist or has been cleaned up.'}
      />
    );
  }

  return (
    <AssetsSupported.Provider value={!!data.instance?.assetsSupported}>
      <Run client={client} run={data.pipelineRunOrError} runId={runId} />
    </AssetsSupported.Provider>
  );
};

export const RUN_ROOT_QUERY = gql`
  query RunRootQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      __typename
      ... on PipelineRun {
        pipeline {
          __typename
          ... on PipelineReference {
            name
            solidSelection
          }
        }
        ...RunFragment
      }
    }
    instance {
      assetsSupported
    }
  }

  ${RunFragments.RunFragment}
`;

const Mono = styled.span`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 600;
`;
