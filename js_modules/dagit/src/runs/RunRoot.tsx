import {gql, useApolloClient, useQuery} from '@apollo/client';
import {IBreadcrumbProps, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components';

import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';
import {AssetsSupported} from 'src/runs/AssetsSupported';
import {Run} from 'src/runs/Run';
import {RunFragments} from 'src/runs/RunFragments';
import {RunStatusTag} from 'src/runs/RunStatusTag';
import {RunRootQuery} from 'src/runs/types/RunRootQuery';
import {Group} from 'src/ui/Group';
import {Spinner} from 'src/ui/Spinner';
import {FontFamily} from 'src/ui/styles';

export const RunRoot = (props: RouteComponentProps<{runId: string}>) => {
  const {runId} = props.match.params;

  const {data, loading, error} = useQuery<RunRootQuery>(RUN_ROOT_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    variables: {runId},
  });

  const run =
    data?.pipelineRunOrError.__typename === 'PipelineRun' ? data.pipelineRunOrError : null;

  const lastBreadcrumb = () => {
    if (loading) {
      return <Spinner purpose="body-text" />;
    }
    if (error || !run) {
      return <Mono>{runId}</Mono>;
    }

    return (
      <div style={{fontWeight: 'normal'}}>
        <Group direction="row" spacing={8} alignItems="center">
          <Mono>{run.id?.slice(0, 8)}</Mono>
          <RunStatusTag status={run.status} />
        </Group>
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
        overflow: 'hidden',
      }}
    >
      <TopNav breadcrumbs={breadcrumbs} />
      <RunById data={data} runId={runId} />
    </div>
  );
};

const RunById: React.FC<{data: RunRootQuery | undefined; runId: string}> = (props) => {
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

const Mono = styled.span`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 600;
`;

const RUN_ROOT_QUERY = gql`
  query RunRootQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      __typename
      ... on PipelineRun {
        id
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
