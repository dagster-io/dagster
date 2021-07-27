import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {RouteComponentProps, Link} from 'react-router-dom';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';
import {FontFamily} from '../ui/styles';

import {Run} from './Run';
import {RunConfigDialog, RunDetails} from './RunDetails';
import {RunFragments} from './RunFragments';
import {RunStatusTag} from './RunStatusTag';
import {RunRootQuery} from './types/RunRootQuery';

export const RunRoot = (props: RouteComponentProps<{runId: string}>) => {
  const {runId} = props.match.params;

  const {data, loading} = useQuery<RunRootQuery>(RUN_ROOT_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    variables: {runId},
  });

  const run =
    data?.pipelineRunOrError.__typename === 'PipelineRun' ? data.pipelineRunOrError : null;
  const snapshotID = run?.pipelineSnapshotId;

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
      <Box
        background={Colors.WHITE}
        padding={{top: 16, bottom: 12, horizontal: 20}}
        border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
        flex={{direction: 'row', alignItems: 'flex-start'}}
        style={{position: 'relative', zIndex: 1}}
      >
        <PageHeader
          title={
            <Group direction="row" spacing={12} alignItems="flex-end">
              <Heading style={{fontFamily: FontFamily.monospace}}>{runId.slice(0, 8)}</Heading>
              {loading || !run ? null : (
                <div style={{position: 'relative', top: '-2px'}}>
                  <RunStatusTag status={run.status} />
                </div>
              )}
            </Group>
          }
          icon="history"
          description={
            <>
              <Link to="/instance/runs">Run</Link> of{' '}
              {run ? (
                <PipelineReference
                  pipelineName={run?.pipeline.name}
                  pipelineHrefContext={'repo-unknown'}
                  snapshotId={snapshotID}
                  mode={run?.mode}
                />
              ) : (
                <span>…</span>
              )}
            </>
          }
          metadata={run ? <RunDetails run={run} loading={loading} /> : null}
          right={run ? <RunConfigDialog run={run} /> : null}
        />
      </Box>
      <RunById data={data} runId={runId} />
    </div>
  );
};

const RunById: React.FC<{data: RunRootQuery | undefined; runId: string}> = (props) => {
  const {data, runId} = props;
  useDocumentTitle(`Run: ${runId}`);

  if (!data || !data.pipelineRunOrError) {
    return <Run run={undefined} runId={runId} />;
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

  return <Run run={data.pipelineRunOrError} runId={runId} />;
};

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
  }

  ${RunFragments.RunFragment}
`;
