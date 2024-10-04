import {
  Alert,
  Box,
  Colors,
  Group,
  Heading,
  Icon,
  MiddleTruncate,
  Mono,
  Spinner,
  Subheading,
  Tag,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AllIndividualEventsButton} from './AllIndividualEventsButton';
import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {AssetEventSystemTags} from './AssetEventSystemTags';
import {ChangedReasonsTag} from './ChangedReasons';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
import {StaleReasonsTag} from './Stale';
import {AssetEventGroup} from './groupByPartition';
import {AssetKey} from './types';
import {
  AssetPartitionDetailQuery,
  AssetPartitionDetailQueryVariables,
  AssetPartitionLatestRunFragment,
  AssetPartitionStaleQuery,
  AssetPartitionStaleQueryVariables,
} from './types/AssetPartitionDetail.types';
import {AssetObservationFragment} from './types/useRecentAssetEvents.types';
import {ASSET_MATERIALIZATION_FRAGMENT, ASSET_OBSERVATION_FRAGMENT} from './useRecentAssetEvents';
import {gql, useQuery} from '../apollo-client';
import {Timestamp} from '../app/time/Timestamp';
import {AssetStaleDataFragment} from '../asset-data/types/AssetStaleStatusDataProvider.types';
import {isHiddenAssetGroupJob, stepKeyForAsset} from '../asset-graph/Utils';
import {ChangeReason, RunStatus, StaleStatus} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const AssetPartitionDetailLoader = (props: {assetKey: AssetKey; partitionKey: string}) => {
  const result = useQuery<AssetPartitionDetailQuery, AssetPartitionDetailQueryVariables>(
    ASSET_PARTITION_DETAIL_QUERY,
    {variables: {assetKey: props.assetKey, partitionKey: props.partitionKey}},
  );

  const stale = useQuery<AssetPartitionStaleQuery, AssetPartitionStaleQueryVariables>(
    ASSET_PARTITION_STALE_QUERY,
    {variables: {assetKey: props.assetKey, partitionKey: props.partitionKey}},
  );

  const {materializations, observations, hasLineage, latestRunForPartition} = useMemo(() => {
    if (result.data?.assetNodeOrError?.__typename !== 'AssetNode') {
      return {
        materializations: [],
        observations: [],
        hasLineage: false,
        latestRunForPartition: null,
      };
    }

    return {
      stepKey: stepKeyForAsset(result.data.assetNodeOrError),
      latestRunForPartition: result.data.assetNodeOrError.latestRunForPartition,
      materializations: [...result.data.assetNodeOrError.assetMaterializations].sort(
        (a, b) => Number(b.timestamp) - Number(a.timestamp),
      ),
      observations: [...result.data.assetNodeOrError.assetObservations].sort(
        (a, b) => Number(b.timestamp) - Number(a.timestamp),
      ),
      hasLineage: result.data.assetNodeOrError.assetMaterializations.some(
        (m) => m.assetLineage.length > 0,
      ),
    };
  }, [result.data]);

  const {staleStatus, staleCauses} = useMemo(() => {
    if (stale.data?.assetNodeOrError?.__typename !== 'AssetNode') {
      return {
        staleCauses: [],
        staleStatus: StaleStatus.FRESH,
      };
    }
    return {
      staleStatus: stale.data.assetNodeOrError.staleStatus,
      staleCauses: stale.data.assetNodeOrError.staleCauses,
    };
  }, [stale.data]);

  const latest = materializations[0];

  if (result.loading || !result.data) {
    return <AssetPartitionDetailEmpty partitionKey={props.partitionKey} />;
  }

  return (
    <AssetPartitionDetail
      hasLineage={hasLineage}
      hasStaleLoadingState={stale.loading}
      latestRunForPartition={latestRunForPartition}
      staleStatus={staleStatus}
      staleCauses={staleCauses}
      assetKey={props.assetKey}
      group={{
        latest: latest || null,
        timestamp: latest?.timestamp,
        partition: props.partitionKey,
        all: [...materializations, ...observations].sort(
          (a, b) => Number(b.timestamp) - Number(a.timestamp),
        ),
      }}
    />
  );
};

export const ASSET_PARTITION_DETAIL_QUERY = gql`
  query AssetPartitionDetailQuery($assetKey: AssetKeyInput!, $partitionKey: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        opNames
        latestRunForPartition(partition: $partitionKey) {
          id
          ...AssetPartitionLatestRunFragment
        }
        assetMaterializations(partitions: [$partitionKey]) {
          ... on MaterializationEvent {
            runId
            ...AssetMaterializationFragment
          }
        }
        assetObservations(partitions: [$partitionKey]) {
          ... on ObservationEvent {
            runId
            ...AssetObservationFragment
          }
        }
      }
    }
  }
  fragment AssetPartitionLatestRunFragment on Run {
    id
    status
    endTime
  }

  ${ASSET_MATERIALIZATION_FRAGMENT}
  ${ASSET_OBSERVATION_FRAGMENT}
`;

export const ASSET_PARTITION_STALE_QUERY = gql`
  query AssetPartitionStaleQuery($assetKey: AssetKeyInput!, $partitionKey: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        staleStatus(partition: $partitionKey)
        staleCauses(partition: $partitionKey) {
          key {
            path
          }
          reason
          category
          dependency {
            path
          }
        }
      }
    }
  }
`;

export const AssetPartitionDetail = ({
  assetKey,
  stepKey,
  group,
  hasLineage,
  hasLoadingState,
  hasStaleLoadingState,
  latestRunForPartition,
  staleCauses,
  staleStatus,
  changedReasons,
}: {
  assetKey: AssetKey;
  group: AssetEventGroup;
  latestRunForPartition: AssetPartitionLatestRunFragment | null;
  hasLineage: boolean;
  hasLoadingState?: boolean;
  hasStaleLoadingState?: boolean;
  stepKey?: string;
  staleCauses?: AssetStaleDataFragment['staleCauses'];
  staleStatus?: AssetStaleDataFragment['staleStatus'];
  changedReasons?: ChangeReason[];
}) => {
  const {latest, partition, all} = group;

  // Somewhat confusing, but we have `latestEventRun`, the run that generated the
  // last successful materialization and we also have `currentRun`, which may have failed!
  const latestEventRun = latest?.runOrError?.__typename === 'Run' ? latest.runOrError : null;

  const currentRun =
    latestRunForPartition?.id !== latestEventRun?.id ? latestRunForPartition : null;
  const currentRunStatusMessage =
    currentRun?.status === RunStatus.STARTED
      ? 'that targets this partition has started .'
      : currentRun?.status === RunStatus.STARTING
      ? 'that targets this partition is starting.'
      : currentRun?.status === RunStatus.QUEUED
      ? 'that targets this partition is queued.'
      : undefined;

  const repositoryOrigin = latestEventRun?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  const observationsAboutLatest =
    latest?.__typename === 'MaterializationEvent'
      ? (group.all.filter(
          (e) =>
            e.__typename === 'ObservationEvent' && Number(e.timestamp) > Number(latest.timestamp),
        ) as AssetObservationFragment[])
      : [];

  return (
    <Box padding={{horizontal: 24, bottom: 24}} style={{flex: 1}}>
      <Box padding={{vertical: 24}} border="bottom" flex={{alignItems: 'center'}}>
        {partition ? (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) auto auto',
              gap: 12,
              alignItems: 'center',
            }}
            data-tooltip={partition}
            data-tooltip-style={PartitionHeadingTooltipStyle}
          >
            <Heading>
              <MiddleTruncate text={partition} />
            </Heading>
            {hasLoadingState ? (
              <Spinner purpose="body-text" />
            ) : latest ? (
              <Tag intent="success">Materialized</Tag>
            ) : undefined}
            {hasStaleLoadingState ? (
              <Spinner purpose="body-text" />
            ) : (
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <StaleReasonsTag
                  liveData={staleCauses && staleStatus ? {staleCauses, staleStatus} : undefined}
                  assetKey={assetKey}
                />
                <ChangedReasonsTag changedReasons={changedReasons} assetKey={assetKey} />
              </Box>
            )}
          </div>
        ) : (
          <Heading color={Colors.textLight()}>No partition selected</Heading>
        )}
        <div style={{flex: 1}} />
      </Box>
      {currentRun?.status === RunStatus.FAILURE && (
        <FailedRunSinceMaterializationBanner
          run={currentRun}
          stepKey={stepKey}
          padding={{horizontal: 0, vertical: 16}}
          border="bottom"
        />
      )}
      {currentRun && currentRunStatusMessage && (
        <Alert
          intent="info"
          icon={<Spinner purpose="body-text" />}
          title={
            <div style={{fontWeight: 400}}>
              Run <Link to={`/runs/${currentRun.id}`}>{titleForRun(currentRun)}</Link>{' '}
              {currentRunStatusMessage}
            </div>
          }
        />
      )}

      <Box
        style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, minHeight: 76}}
        border="bottom"
        padding={{vertical: 16}}
      >
        {!latest ? (
          <Box flex={{gap: 4, direction: 'column'}}>
            <Subheading>Latest materialization</Subheading>
            <Box flex={{gap: 4}}>
              <Icon name="materialization" />
              None
            </Box>
          </Box>
        ) : (
          <Box flex={{gap: 4, direction: 'column'}}>
            <Subheading>
              {latest.__typename === 'MaterializationEvent'
                ? 'Latest materialization'
                : 'Latest observation'}
            </Subheading>
            <Box flex={{gap: 4}} style={{whiteSpace: 'nowrap'}}>
              {latest.__typename === 'MaterializationEvent' ? (
                <Icon name="materialization" />
              ) : (
                <Icon name="observation" />
              )}
              <Timestamp timestamp={{ms: Number(latest.timestamp)}} />
            </Box>
          </Box>
        )}
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Run</Subheading>
          {latestEventRun && latest ? (
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <RunStatusWithStats runId={latestEventRun.id} status={latestEventRun.status} />
              <Link to={linkToRunEvent(latestEventRun, latest)}>
                <Mono>{titleForRun(latestEventRun)}</Mono>
              </Link>
            </Box>
          ) : (
            'None'
          )}
        </Box>
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Job</Subheading>
          {latest && latestEventRun && !isHiddenAssetGroupJob(latestEventRun.pipelineName) ? (
            <Box>
              <Box>
                <PipelineReference
                  showIcon
                  pipelineName={latestEventRun.pipelineName}
                  pipelineHrefContext={repoAddress || 'repo-unknown'}
                  snapshotId={latestEventRun.pipelineSnapshotId}
                  isJob={isThisThingAJob(repo, latestEventRun.pipelineName)}
                />
              </Box>
              <Group direction="row" spacing={8} alignItems="center">
                <Icon name="linear_scale" color={Colors.accentGray()} />
                <Link to={linkToRunEvent(latestEventRun, latest)}>{latest.stepKey}</Link>
              </Group>
            </Box>
          ) : (
            'None'
          )}
        </Box>
        <Box style={{textAlign: 'right'}}>
          <AllIndividualEventsButton
            hasPartitions
            hasLineage={hasLineage}
            events={all}
            disabled={all.length === 0}
          >
            {`View all historical events (${all.length})`}
          </AllIndividualEventsButton>
        </Box>
      </Box>
      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Subheading>Metadata</Subheading>
        <AssetEventMetadataEntriesTable
          event={latest}
          observations={observationsAboutLatest}
          repoAddress={repoAddress}
          showDescriptions
        />
      </Box>
      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Subheading>Tags</Subheading>
        <AssetEventSystemTags event={latest} collapsible />
      </Box>
    </Box>
  );
};

export const AssetPartitionDetailEmpty = ({partitionKey}: {partitionKey?: string}) => (
  <AssetPartitionDetail
    assetKey={{path: ['']}}
    group={{all: [], latest: null, timestamp: '0', partition: partitionKey}}
    latestRunForPartition={null}
    hasLineage={false}
    hasLoadingState
  />
);

const PartitionHeadingTooltipStyle = JSON.stringify({
  background: Colors.backgroundLight(),
  border: `1px solid ${Colors.borderDefault()}`,
  fontSize: '18px',
  fontWeight: '600',
  color: Colors.textDefault(),
});
