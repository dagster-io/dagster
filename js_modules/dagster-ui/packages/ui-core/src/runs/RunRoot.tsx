import {
  Box,
  Colors,
  FontFamily,
  Heading,
  NonIdealState,
  PageHeader,
  Tag,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link, useParams} from 'react-router-dom';

import {Run} from './Run';
import {RunAssetCheckTags} from './RunAssetCheckTags';
import {RunAssetTags} from './RunAssetTags';
import {RUN_PAGE_FRAGMENT} from './RunFragments';
import {RunHeaderActions} from './RunHeaderActions';
import {RunStatusTag} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTimingTags} from './RunTimingTags';
import {getBackfillPath} from './RunsFeedUtils';
import {TickTagForRun} from './TickTagForRun';
import {RunRootQuery, RunRootQueryVariables} from './types/RunRoot.types';
import {gql, useQuery} from '../apollo-client';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {AutomaterializeTagWithEvaluation} from '../assets/AutomaterializeTagWithEvaluation';
import {InstigationSelector} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineReference} from '../pipelines/PipelineReference';
import {isThisThingAJob} from '../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';

export const RunRoot = () => {
  useTrackPageView();

  const {runId} = useParams<{runId: string}>();
  useDocumentTitle(runId ? `Run ${runId.slice(0, 8)}` : 'Run');

  const queryResult = useQuery<RunRootQuery, RunRootQueryVariables>(RUN_ROOT_QUERY, {
    variables: {runId},
  });
  const {data, loading} = queryResult;

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data.pipelineRunOrError : null;
  const snapshotID = run?.pipelineSnapshotId;

  const repoMatch = useRepositoryForRunWithParentSnapshot(run);
  const repoAddress = repoMatch?.match
    ? buildRepoAddress(repoMatch.match.repository.name, repoMatch.match.repositoryLocation.name)
    : null;

  const isJob = useMemo(
    () => !!(run && repoMatch && isThisThingAJob(repoMatch.match, run.pipelineName)),
    [run, repoMatch],
  );

  const automaterializeTag = useMemo(
    () => run?.tags.find((tag) => tag.key === DagsterTag.AssetEvaluationID) || null,
    [run],
  );

  const backfillTag = useMemo(
    () => run?.tags.find((tag) => tag.key === DagsterTag.Backfill),
    [run],
  );

  const tickDetails = useMemo(() => {
    if (repoAddress) {
      const tags = run?.tags || [];
      const tickTag = tags.find((tag) => tag.key === DagsterTag.TickId);

      if (tickTag) {
        const scheduleOrSensor = tags.find(
          (tag) => tag.key === DagsterTag.ScheduleName || tag.key === DagsterTag.SensorName,
        );
        if (scheduleOrSensor) {
          const instigationSelector: InstigationSelector = {
            name: scheduleOrSensor.value,
            repositoryName: repoAddress.name,
            repositoryLocationName: repoAddress.location,
          };
          return {
            tickId: tickTag.value,
            instigationType: scheduleOrSensor.key as
              | DagsterTag.ScheduleName
              | DagsterTag.SensorName,
            instigationSelector,
          };
        }
      }
    }

    return null;
  }, [run, repoAddress]);

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
            backfillTag ? (
              <Heading>
                <Link to="/runs" style={{color: Colors.textLight()}}>
                  All runs
                </Link>
                {' / '}
                <Link
                  to={getBackfillPath(backfillTag.value, !!run?.assetSelection?.length)}
                  style={{color: Colors.textLight()}}
                >
                  {backfillTag.value}
                </Link>
                {' / '}
                {runId.slice(0, 8)}
              </Heading>
            ) : (
              <Heading style={{display: 'flex', flexDirection: 'row', gap: 6}}>
                <Link to="/runs">All Runs</Link>
                <span>/</span>
                <span style={{fontFamily: FontFamily.monospace}}>{runId.slice(0, 8)}</span>
              </Heading>
            )
          }
          tags={
            run ? (
              <Box flex={{direction: 'row', alignItems: 'flex-start', gap: 12, wrap: 'wrap'}}>
                <RunStatusTag status={run.status} />
                {!isHiddenAssetGroupJob(run.pipelineName) ? (
                  <Tag icon="run">
                    Run of{' '}
                    <PipelineReference
                      pipelineName={run?.pipelineName}
                      pipelineHrefContext={repoAddress || 'repo-unknown'}
                      snapshotId={snapshotID}
                      size="small"
                      isJob={isJob}
                    />
                  </Tag>
                ) : null}
                {tickDetails ? (
                  <TickTagForRun
                    instigationSelector={tickDetails.instigationSelector}
                    instigationType={tickDetails.instigationType}
                    tickId={tickDetails.tickId}
                  />
                ) : null}
                <RunAssetTags run={run} />
                <RunAssetCheckTags run={run} />
                <RunTimingTags run={run} loading={loading} />
                {automaterializeTag && run.assetSelection?.length ? (
                  <AutomaterializeTagWithEvaluation
                    assetKeys={run.assetSelection}
                    evaluationId={automaterializeTag.value}
                  />
                ) : null}
              </Box>
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
      ... on Run {
        id
        ...RunPageFragment
      }
    }
  }

  ${RUN_PAGE_FRAGMENT}
`;
