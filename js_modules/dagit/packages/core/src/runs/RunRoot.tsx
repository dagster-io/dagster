import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {NonIdealState} from '../ui/NonIdealState';
import {PageHeader} from '../ui/PageHeader';
import {Popover} from '../ui/Popover';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';
import {FontFamily} from '../ui/styles';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

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
  const repoAddress = React.useMemo(() => {
    const repositoryOrigin = run?.repositoryOrigin;
    if (repositoryOrigin) {
      const {repositoryLocationName, repositoryName} = repositoryOrigin;
      return buildRepoAddress(repositoryName, repositoryLocationName);
    }
    return null;
  }, [run]);

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
        flex={{direction: 'row', alignItems: 'flex-start'}}
        style={{
          position: 'relative',
          zIndex: 1,
        }}
      >
        <PageHeader
          title={
            <Heading style={{fontFamily: FontFamily.monospace, fontSize: '20px'}}>
              {runId.slice(0, 8)}
            </Heading>
          }
          tags={
            run ? (
              <>
                <Popover
                  interactionKind="hover"
                  placement="bottom"
                  content={
                    <Box padding={16}>
                      <RunDetails run={run} loading={loading} />
                    </Box>
                  }
                >
                  <TagWIP icon="info" />
                </Popover>
                <TagWIP icon="run">
                  Run of{' '}
                  <PipelineReference
                    pipelineName={run?.pipeline.name}
                    pipelineHrefContext={repoAddress || 'repo-unknown'}
                    snapshotId={snapshotID}
                    mode={run?.mode}
                    size="small"
                  />
                </TagWIP>
                <RunStatusTag status={run.status} />
              </>
            ) : null
          }
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
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="No run found"
          description="The run with this ID does not exist or has been cleaned up."
        />
      </Box>
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
