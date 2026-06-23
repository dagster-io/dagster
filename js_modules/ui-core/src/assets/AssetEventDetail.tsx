import {Box, Colors, Heading, Icon, Text} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {AssetEventSystemTags} from './AssetEventSystemTags';
import {AssetLineageElements} from './AssetLineageElements';
import {RunlessEventTag} from './RunlessEventTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {isRunlessEvent} from './isRunlessEvent';
import {
  AssetFailedToMaterializeFragment,
  AssetObservationFragment,
  AssetSuccessfulMaterializationFragment,
} from './types/useRecentAssetEvents.types';
import {Timestamp} from '../app/time/Timestamp';
import {AssetKeyInput} from '../graphql/types';
import {Description} from '../pipelines/Description';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const AssetEventDetail = ({
  event,
  assetKey,
}: {
  assetKey: AssetKeyInput;
  event:
    | AssetSuccessfulMaterializationFragment
    | AssetFailedToMaterializeFragment
    | AssetObservationFragment;
}) => {
  const run = event.runOrError?.__typename === 'Run' ? event.runOrError : null;
  const repositoryOrigin = run?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const assetLineage = event.__typename === 'MaterializationEvent' ? event.assetLineage : [];

  const {icon, label} = useMemo(() => {
    switch (event.__typename) {
      case 'MaterializationEvent':
        return {
          icon: <Icon name="run_success" color={Colors.accentGreen()} size={16} />,
          label: 'Materialized',
        };
      case 'ObservationEvent':
        return {
          icon: <Icon name="observation" color={Colors.accentGreen()} size={16} />,
          label: 'Observed',
        };
      case 'FailedToMaterializeEvent':
        if (event?.materializationFailureType === 'FAILED') {
          return {
            icon: <Icon name="run_failed" color={Colors.accentRed()} size={16} />,
            label: 'Failed',
          };
        } else {
          return {
            icon: <Icon name="status" color={Colors.accentGray()} size={16} />,
            label: 'Skipped',
          };
        }
    }
  }, [event]);

  return (
    <Box padding={{horizontal: 24, bottom: 24}} style={{flex: 1}}>
      <Box padding={{vertical: 24}} border="bottom" flex={{direction: 'column', gap: 8}}>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          <Heading size={20} weight={500}>
            <Timestamp timestamp={{ms: Number(event.timestamp)}} />
          </Heading>
          {isRunlessEvent(event) ? <RunlessEventTag tags={event.tags} /> : undefined}
        </Box>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
          {icon}
          <div style={{overflowWrap: 'break-word', wordBreak: 'break-word'}}>
            {event.partition ? (
              <>
                Partition{' '}
                <Link
                  to={assetDetailsPathForKey(assetKey, {
                    view: 'partitions',
                    partition: event.partition,
                  })}
                >
                  {event.partition}
                </Link>{' '}
                {label.toLowerCase()}
              </>
            ) : (
              label
            )}
            {run && (
              <>
                {' '}
                in run{' '}
                <Link to={linkToRunEvent(run, event)}>
                  <Text size={14} family="mono">
                    {titleForRun(run)}
                  </Text>
                </Link>
              </>
            )}
          </div>
        </Box>
      </Box>

      {event.description && (
        <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
          <Heading size={14} weight={600}>
            Description
          </Heading>
          <Description description={event.description} />
        </Box>
      )}

      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Heading size={14} weight={600}>
          Metadata
        </Heading>
        <AssetEventMetadataEntriesTable
          repoAddress={repoAddress}
          assetKey={assetKey}
          event={event}
          showDescriptions
        />
      </Box>

      <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
        <Heading size={14} weight={600}>
          Tags
        </Heading>
        <AssetEventSystemTags event={event} collapsible />
      </Box>

      {assetLineage.length > 0 && (
        <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
          <Heading size={14} weight={600}>
            Parent materializations
          </Heading>
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
      <Heading size={20} weight={500} color="textLight">
        No event selected
      </Heading>
    </Box>
    <Box
      style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16}}
      border="bottom"
      padding={{vertical: 16}}
    >
      <Box flex={{gap: 4, direction: 'column'}}>
        <Heading size={14} weight={600}>
          Event
        </Heading>
      </Box>
      <Box flex={{gap: 4, direction: 'column'}} style={{minHeight: 64}}>
        <Heading size={14} weight={600}>
          Run
        </Heading>
        —
      </Box>
      <Box flex={{gap: 4, direction: 'column'}}>
        <Heading size={14} weight={600}>
          Job
        </Heading>
        —
      </Box>
    </Box>

    <Box padding={{top: 24}} flex={{direction: 'column', gap: 8}}>
      <Heading size={14} weight={600}>
        Metadata
      </Heading>
      <AssetEventMetadataEntriesTable event={null} repoAddress={null} showDescriptions />
    </Box>
  </Box>
);
