import {Box, Colors, Group, Heading, Icon, Mono, Subheading, Tag} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun, linkToRunEvent} from '../runs/RunUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {AllIndividualEventsLink} from './AssetEventsTable';
import {AssetEventGroup} from './groupByPartition';

export const AssetPartitionDetail: React.FC<{
  group: AssetEventGroup;
  hasLineage: boolean;
}> = ({group, hasLineage}) => {
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
    <Box padding={{horizontal: 24}} background={Colors.Gray10} style={{flex: 1}}>
      <Box
        padding={{vertical: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{alignItems: 'center'}}
      >
        {partition ? (
          <Box flex={{gap: 12}}>
            <Heading>{partition}</Heading>
            {latest ? <Tag intent="success">Materialized</Tag> : <Tag intent="none">Missing</Tag>}
          </Box>
        ) : (
          <Heading>&nbsp;</Heading>
        )}
        <div style={{flex: 1}} />
      </Box>
      <Box
        style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16}}
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
            <Box flex={{gap: 4}}>
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

export const AssetPartitionDetailEmpty = () => (
  <AssetPartitionDetail
    group={{all: [], latest: null, timestamp: '0', partition: undefined}}
    hasLineage={false}
  />
);
