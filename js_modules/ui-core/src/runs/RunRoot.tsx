import {
  Box,
  Colors,
  FontFamily,
  Heading,
  Icon,
  NonIdealState,
  PageHeader,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link, useParams} from 'react-router-dom';

import {Run} from './Run';
import {RUN_PAGE_FRAGMENT} from './RunFragments';
import {RunHeaderActions} from './RunHeaderActions';
import {RunHeaderTags} from './RunHeaderTags';
import {DagsterTag} from './RunTag';
import {getBackfillPath} from './RunsFeedUtils';
import {getExternalRunUrl, isExternalRun} from './externalRuns';
import {gql, useQuery} from '../apollo-client';
import {RunPageFragment} from './types/RunFragments.types';
import {RunRootQuery, RunRootQueryVariables} from './types/RunRoot.types';
import {useRunRepoInfo} from './useRunRepoInfo';
import {useTrackPageView} from '../app/analytics';
import {useIsMobile} from '../app/layout/IsMobileContext';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {shortenId} from '../util/shortenId';

export const RunRoot = () => {
  useTrackPageView();

  const {runId} = useParams<{runId: string}>();
  useDocumentTitle(runId ? `Runs | ${shortenId(runId)}` : 'Runs');

  const queryResult = useQuery<RunRootQuery, RunRootQueryVariables>(RUN_ROOT_QUERY, {
    variables: {runId},
  });
  const {data, loading} = queryResult;

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data.pipelineRunOrError : null;
  const {repoAddress, isJob} = useRunRepoInfo(run);
  // On mobile the tags move to the run's Details tab, which external runs don't render.
  const isMobile = useIsMobile();
  const showHeaderTags = run && (!isMobile || isExternalRun(run));

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
          title={<RunHeaderTitle run={run} runId={runId} />}
          tags={
            showHeaderTags ? (
              <RunHeaderTags run={run} repoAddress={repoAddress} isJob={isJob} loading={loading} />
            ) : null
          }
          right={run ? <RunHeaderActions run={run} isJob={isJob} /> : null}
        />
      </Box>
      <RunById data={data} runId={runId} />
    </div>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunRoot;

const RunById = (props: {data: RunRootQuery | undefined; runId: string}) => {
  const {data, runId} = props;

  if (!data || !data.pipelineRunOrError) {
    return null;
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

  if (isExternalRun(data.pipelineRunOrError)) {
    const externalUrl = getExternalRunUrl(data.pipelineRunOrError);
    if (externalUrl) {
      return (
        <Box padding={{vertical: 64}}>
          <NonIdealState
            icon="job"
            title="This run was remotely executed"
            description={
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                <a href={externalUrl} target="_blank" rel="noreferrer">
                  View the execution logs
                </a>
                <Icon name="open_in_new" size={16} style={{marginLeft: 8}} />
              </Box>
            }
          />
        </Box>
      );
    } else {
      return (
        <Box padding={{vertical: 64}}>
          <NonIdealState
            icon="job"
            title="No external URL found"
            description="This run was executed externally, but does not have an external URL."
          />
        </Box>
      );
    }
  }

  return <Run run={data.pipelineRunOrError} runId={runId} />;
};

const RUN_ROOT_QUERY = gql`
  query RunRootQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        ...RunPageFragment
      }
    }
  }

  ${RUN_PAGE_FRAGMENT}
`;

const RunHeaderTitle = ({run, runId}: {run: RunPageFragment | null; runId: string}) => {
  const backfillTag = useMemo(
    () => run?.tags.find((tag) => tag.key === DagsterTag.Backfill),
    [run],
  );

  if (backfillTag) {
    return (
      <Heading size={16} weight={600}>
        <Link to="/runs" style={{color: Colors.textLight()}}>
          Runs
        </Link>
        {' / '}
        <Link to={getBackfillPath(backfillTag.value, 'runs')} style={{color: Colors.textLight()}}>
          {backfillTag.value}
        </Link>
        {' / '}
        {shortenId(runId)}
      </Heading>
    );
  }

  return (
    <Heading size={16} weight={600} style={{display: 'flex', flexDirection: 'row', gap: 6}}>
      <Link to="/runs">Runs</Link>
      <span>/</span>
      <span style={{fontFamily: FontFamily.monospace}}>{shortenId(runId)}</span>
    </Heading>
  );
};
