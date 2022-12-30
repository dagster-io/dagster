import {useQuery} from '@apollo/client';
import {Box, Colors, Group, Heading, Icon, Mono, Spinner, Subheading, Tag} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {graphql} from '../graphql';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun, linkToRunEvent} from '../runs/RunUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AllIndividualEventsLink} from './AllIndividualEventsLink';
import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {AssetEventGroup} from './groupByPartition';
import {AssetKey} from './types';

export const AssetPartitionDetailLoader: React.FC<{assetKey: AssetKey; partitionKey: string}> = (
  props,
) => {
  const result = useQuery(ASSET_PARTITION_DETAIL_QUERY, {
    variables: {
      assetKey: props.assetKey,
      partitionKey: props.partitionKey,
    },
  });

  if (result.loading || !result.data) {
    return <AssetPartitionDetailEmpty partitionKey={props.partitionKey} />;
  }

  const events =
    result.data?.assetNodeOrError?.__typename === 'AssetNode'
      ? result.data.assetNodeOrError.assetMaterializations
      : [];

  const hasLineage = events.some((m) => m.assetLineage.length > 0);

  return (
    <AssetPartitionDetail
      hasLineage={hasLineage}
      group={{
        latest: events[0],
        all: events,
        timestamp: events[0]?.timestamp,
        partition: props.partitionKey,
      }}
    />
  );
};

const ASSET_PARTITION_DETAIL_QUERY = graphql(`
  query AssetPartitionDetailQuery($assetKey: AssetKeyInput!, $partitionKey: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      __typename
      ... on AssetNode {
        id
        assetMaterializations(partitions: [$partitionKey]) {
          ... on MaterializationEvent {
            runId
            ...AssetMaterializationFragment
          }
        }
      }
    }
  }
`);

export const AssetPartitionDetail: React.FC<{
  group: AssetEventGroup;
  hasLineage: boolean;
  hasLoadingState?: boolean;
}> = ({group, hasLineage, hasLoadingState}) => {
  const {latest, partition, all} = group;
  const run = latest?.runOrError?.__typename === 'Run' ? latest.runOrError : null;
  const repositoryOrigin = run?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  const observationsAboutLatest =
    latest?.__typename === 'MaterializationEvent'
      ? group.all.filter(
          (e) =>
            e.__typename === 'ObservationEvent' && Number(e.timestamp) > Number(latest.timestamp),
        )
      : [];

  return (
    <Box padding={{horizontal: 24}} style={{flex: 1}}>
      <Box
        padding={{vertical: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center'}}
      >
        {partition ? (
          <Box flex={{gap: 12, alignItems: 'center'}}>
            <Heading>{partition}</Heading>
            {hasLoadingState ? (
              <Spinner purpose="body-text" />
            ) : latest ? (
              <Tag intent="success">Materialized</Tag>
            ) : (
              <Tag intent="none">Missing</Tag>
            )}
          </Box>
        ) : (
          <Heading color={Colors.Gray400}>No Partition Selected</Heading>
        )}
        <div style={{flex: 1}} />
      </Box>
      <Box
        style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, minHeight: 76}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        padding={{vertical: 16}}
      >
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Latest Event</Subheading>
          {!latest ? (
            <Box flex={{gap: 4}}>
              <Icon name="materialization" />
              None
            </Box>
          ) : (
            <Box flex={{gap: 4}} style={{whiteSpace: 'nowrap'}}>
              {latest.__typename === 'MaterializationEvent' ? (
                <Icon name="materialization" />
              ) : (
                <Icon name="observation" />
              )}
              <Timestamp timestamp={{ms: Number(latest.timestamp)}} />
              {all.length > 1 && (
                <AllIndividualEventsLink hasPartitions hasLineage={hasLineage} events={all}>
                  {`(${all.length} events)`}
                </AllIndividualEventsLink>
              )}
            </Box>
          )}
        </Box>
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Run</Subheading>
          {latest?.runOrError?.__typename === 'Run' ? (
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <RunStatusWithStats
                runId={latest.runOrError.runId}
                status={latest.runOrError.status}
              />
              <Link to={linkToRunEvent(latest.runOrError, latest)}>
                <Mono>{titleForRun(latest.runOrError)}</Mono>
              </Link>
            </Box>
          ) : (
            'None'
          )}
        </Box>
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Job</Subheading>
          {latest && run && !isHiddenAssetGroupJob(run.pipelineName) ? (
            <Box>
              <Box>
                <PipelineReference
                  showIcon
                  pipelineName={run.pipelineName}
                  pipelineHrefContext={repoAddress || 'repo-unknown'}
                  snapshotId={run.pipelineSnapshotId}
                  isJob={isThisThingAJob(repo, run.pipelineName)}
                />
              </Box>
              <Group direction="row" spacing={8} alignItems="center">
                <Icon name="linear_scale" color={Colors.Gray400} />
                <Link to={linkToRunEvent(run, latest)}>{latest.stepKey}</Link>
              </Group>
            </Box>
          ) : (
            'None'
          )}
        </Box>
      </Box>
      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Subheading>Metadata</Subheading>
        <AssetEventMetadataEntriesTable event={latest} observations={observationsAboutLatest} />
      </Box>
    </Box>
  );
};

export const AssetPartitionDetailEmpty = ({partitionKey}: {partitionKey?: string}) => (
  <AssetPartitionDetail
    group={{all: [], latest: null, timestamp: '0', partition: partitionKey}}
    hasLineage={false}
    hasLoadingState
  />
);
