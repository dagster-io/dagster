import {Box, Colors, Heading, Icon, Mono, Subheading} from '@dagster-io/ui-components';
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
        return {
          icon: <Icon name="run_failed" color={Colors.accentRed()} size={16} />,
          label: 'Failed',
        };
    }
  }, [event.__typename]);

  return (
    <Box padding={{horizontal: 24, bottom: 24}} style={{flex: 1}}>
      <Box padding={{vertical: 24}} border="bottom" flex={{direction: 'column', gap: 8}}>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          <Heading>
            <Timestamp timestamp={{ms: Number(event.timestamp)}} />
          </Heading>
          {isRunlessEvent(event) ? <RunlessEventTag tags={event.tags} /> : undefined}
        </Box>
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          {icon}
          {event.partition ? (
            <>
              Partition
              <Link
                to={assetDetailsPathForKey(assetKey, {
                  view: 'partitions',
                  partition: event.partition,
                })}
              >
                {event.partition}
              </Link>
              {label.toLowerCase()}
            </>
          ) : (
            <span>{label}</span>
          )}
          {run && (
            <>
              <span>in run</span>
              <Link to={linkToRunEvent(run, event)}>
                <Mono>{titleForRun(run)}</Mono>
              </Link>
            </>
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
