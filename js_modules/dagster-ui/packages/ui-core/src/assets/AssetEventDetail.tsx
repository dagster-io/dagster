import {Box, Colors, Group, Heading, Icon, Mono, Subheading} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {AssetEventSystemTags} from './AssetEventSystemTags';
import {AssetLineageElements} from './AssetLineageElements';
import {RunlessEventTag} from './RunlessEventTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {isRunlessEvent} from './isRunlessEvent';
import {
  AssetMaterializationFragment,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {Timestamp} from '../app/time/Timestamp';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const AssetEventDetail = ({
  event,
  assetKey,
  hidePartitionLinks = false,
}: {
  assetKey: AssetKeyInput;
  event: AssetMaterializationFragment | AssetObservationFragment;
  hidePartitionLinks?: boolean;
}) => {
  const run = event.runOrError?.__typename === 'Run' ? event.runOrError : null;
  const repositoryOrigin = run?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);
  const assetLineage = event.__typename === 'MaterializationEvent' ? event.assetLineage : [];

  return (
    <Box padding={{horizontal: 24, bottom: 24}} style={{flex: 1}}>
      <Box padding={{vertical: 24}} border="bottom" flex={{alignItems: 'center', gap: 12}}>
        <Heading>
          <Timestamp timestamp={{ms: Number(event.timestamp)}} />
        </Heading>
        {isRunlessEvent(event) ? <RunlessEventTag tags={event.tags} /> : undefined}
      </Box>
      <Box
        style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16}}
        border="bottom"
        padding={{vertical: 16}}
      >
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Event</Subheading>
          {event.__typename === 'MaterializationEvent' ? (
            <Box flex={{gap: 4}}>
              <Icon name="materialization" />
              Materialization
            </Box>
          ) : (
            <Box flex={{gap: 4}}>
              <Icon name="observation" />
              Observation
            </Box>
          )}
        </Box>
        {event.partition && (
          <Box flex={{gap: 4, direction: 'column'}}>
            <Subheading>Partition</Subheading>
            {hidePartitionLinks ? (
              event.partition
            ) : (
              <>
                <Link
                  to={assetDetailsPathForKey(assetKey, {
                    view: 'partitions',
                    partition: event.partition,
                  })}
                >
                  {event.partition}
                </Link>
                <Link
                  to={assetDetailsPathForKey(assetKey, {
                    view: 'partitions',
                    partition: event.partition,
                    showAllEvents: true,
                  })}
                >
                  View all partition events
                </Link>
              </>
            )}
          </Box>
        )}
        <Box flex={{gap: 4, direction: 'column'}} style={{minHeight: 64}}>
          <Subheading>Run</Subheading>
          {run ? (
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <RunStatusWithStats runId={run.id} status={run.status} />
              <Link to={linkToRunEvent(run, event)}>
                <Mono>{titleForRun(run)}</Mono>
              </Link>
            </Box>
          ) : (
            '—'
          )}
        </Box>
        <Box flex={{gap: 4, direction: 'column'}}>
          <Subheading>Job</Subheading>
          {run && !isHiddenAssetGroupJob(run.pipelineName) ? (
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
                <Icon name="linear_scale" color={Colors.accentGray()} />
                <Link to={linkToRunEvent(run, event)}>{event.stepKey}</Link>
              </Group>
            </Box>
          ) : (
            '—'
          )}
        </Box>
      </Box>

      {event.description && (
        <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
          <Subheading>Description</Subheading>
          <Description description={event.description} />
        </Box>
      )}

      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Subheading>Metadata</Subheading>
        <AssetEventMetadataEntriesTable
          repoAddress={repoAddress}
          assetKey={assetKey}
          event={event}
          showDescriptions
        />
      </Box>

      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Subheading>Tags</Subheading>
        <AssetEventSystemTags event={event} collapsible />
      </Box>

      {assetLineage.length > 0 && (
        <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
          <Subheading>Parent materializations</Subheading>
          <AssetLineageElements elements={assetLineage} timestamp={event.timestamp} />
        </Box>
      )}
    </Box>
  );
};

export const AssetEventDetailEmpty = () => (
  <Box padding={{horizontal: 24}} style={{flex: 1}}>
    <Box
      padding={{vertical: 24}}
      border="bottom"
      flex={{alignItems: 'center', justifyContent: 'space-between'}}
    >
      <Heading color={Colors.textLight()}>No event selected</Heading>
    </Box>
    <Box
      style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16}}
      border="bottom"
      padding={{vertical: 16}}
    >
      <Box flex={{gap: 4, direction: 'column'}}>
        <Subheading>Event</Subheading>
      </Box>
      <Box flex={{gap: 4, direction: 'column'}} style={{minHeight: 64}}>
        <Subheading>Run</Subheading>—
      </Box>
      <Box flex={{gap: 4, direction: 'column'}}>
        <Subheading>Job</Subheading>—
      </Box>
    </Box>

    <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
      <Subheading>Metadata</Subheading>
      <AssetEventMetadataEntriesTable event={null} repoAddress={null} showDescriptions />
    </Box>
  </Box>
);
