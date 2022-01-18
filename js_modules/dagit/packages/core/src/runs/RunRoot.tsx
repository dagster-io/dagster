import {gql, useQuery} from '@apollo/client';
import {Box, NonIdealState, PageHeader, Popover, TagWIP, Heading, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {PipelineReference} from '../pipelines/PipelineReference';
import {isThisThingAJob} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';

import {Run} from './Run';
import {RunConfigDialog, RunDetails} from './RunDetails';
import {RunFragments} from './RunFragments';
import {RunStatusTag} from './RunStatusTag';
import {RunRootQuery} from './types/RunRootQuery';

export const RunRoot = () => {
  const {runId} = useParams<{runId: string}>();

  const {data, loading} = useQuery<RunRootQuery>(RUN_ROOT_QUERY, {
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    variables: {runId},
  });

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data.pipelineRunOrError : null;
  const snapshotID = run?.pipelineSnapshotId;

  const repoMatch = useRepositoryForRun(run);
  const repoAddress = repoMatch?.match
    ? buildRepoAddress(repoMatch.match.repository.name, repoMatch.match.repositoryLocation.name)
    : null;

  const isJob = React.useMemo(
    () => !!(run && repoMatch && isThisThingAJob(repoMatch.match, run.pipelineName)),
    [run, repoMatch],
  );

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
                    pipelineName={run?.pipelineName}
                    pipelineHrefContext={repoAddress || 'repo-unknown'}
                    snapshotId={snapshotID}
                    size="small"
                    isJob={isJob}
                  />
                </TagWIP>
                <RunStatusTag status={run.status} />
              </>
            ) : null
          }
          right={run ? <RunConfigDialog run={run} isJob={isJob} /> : null}
        />
      </Box>
      <RunById data={data} runId={runId} />
    </div>
  );
};

const RunById: React.FC<{data: RunRootQuery | undefined; runId: string}> = (props) => {
  const {data, runId} = props;

  if (!data || !data.pipelineRunOrError) {
    return <Run run={undefined} runId={runId} />;
  }

  if (data.pipelineRunOrError.__typename !== 'Run') {
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
      ... on Run {
        id
        ...RunFragment
      }
    }
  }

  ${RunFragments.RunFragment}
`;
