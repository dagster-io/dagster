import {
  Box,
  Caption,
  CaptionMono,
  Colors,
  FontFamily,
  Icon,
  Popover,
  Skeleton,
  Subtitle2,
  useViewport,
} from '@dagster-io/ui-components';
import {memo, useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {RunlessEventTag} from './RunlessEventTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {isRunlessEvent} from './isRunlessEvent';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {Timestamp} from '../app/time/Timestamp';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
import {titleForRun} from '../runs/RunUtils';
import {batchRunsForTimeline} from '../runs/batchRunsForTimeline';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const INNER_TICK_WIDTH = 4;

type AssetEventType = ReturnType<typeof useRecentAssetEvents>['events'][0];
type Props = {
  assetKey: AssetKey;
  events?: AssetEventType[];
  loading: boolean;
};

export const RecentUpdatesTimelineForAssetKey = memo((props: {assetKey: AssetKey}) => {
  const data = useRecentAssetEvents(props.assetKey, 100, [
    AssetEventHistoryEventTypeSelector.MATERIALIZATION,
    AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
    AssetEventHistoryEventTypeSelector.OBSERVATION,
  ]);
  return (
    <RecentUpdatesTimeline assetKey={props.assetKey} events={data.events} loading={data.loading} />
  );
});

export const RecentUpdatesTimeline = ({assetKey, events, loading}: Props) => {
  const {containerProps, viewport} = useViewport();

  const enrichedEvents = useMemo(() => {
    const seenTimestamps = new Set();
    return (events ?? [])
      .map((event) => {
        if (
          event.__typename === 'MaterializationEvent' ||
          event.__typename === 'FailedToMaterializeEvent'
        ) {
          return event;
        }

        const timestampEntries = event.metadataEntries.filter(
          (entry) => entry.__typename === 'TimestampMetadataEntry',
        );

        const lastUpdated = timestampEntries.find(
          (entry) => entry.label === 'dagster/last_updated_timestamp',
        );

        // The metadata timestamp is in seconds.
        const lastUpdatedSec = lastUpdated?.timestamp;
        const ts = lastUpdatedSec ? lastUpdatedSec * 1000 : event.timestamp;

        if (!seenTimestamps.has(ts)) {
          seenTimestamps.add(ts);
          return {
            ...event,
            timestamp: `${ts}`,
          };
        }

        return null;
      })
      .filter((e): e is AssetEventType => e !== null)
      .sort((a, b) => parseInt(a.timestamp) - parseInt(b.timestamp));
  }, [events]);

  const [startTimestamp, endTimestamp] = getTimelineBounds(enrichedEvents);

  const batchedEvents = useMemo(() => {
    if (!viewport.width || !enrichedEvents.length) {
      return [];
    }

    // Convert events to runs with synthetic 1ms duration
    const eventsAsRuns = enrichedEvents.map((event) => ({
      ...event,
      startTime: parseInt(event.timestamp),
      endTime: parseInt(event.timestamp) + 1,
    }));

    // Use shared batching logic
    return batchRunsForTimeline({
      runs: eventsAsRuns,
      start: startTimestamp,
      end: endTimestamp,
      width: viewport.width,
      minChunkWidth: 1, // INNER_TICK_WIDTH
      minMultipleWidth: 10,
    });
  }, [viewport.width, enrichedEvents, startTimestamp, endTimestamp]);

  const formatDateTime = useFormatDateTime();

  if (loading) {
    return (
      <Box flex={{direction: 'column', gap: 4}}>
        <Box flex={{direction: 'row'}}>
          <Subtitle2>Recent updates</Subtitle2>
        </Box>
        <Skeleton $width="100%" $height={36} />
        <Box padding={{top: 4}} flex={{justifyContent: 'space-between'}}>
          <Skeleton $width={70} $height="1em" style={{minHeight: '1em'}} />
          <Skeleton $width={70} $height="1em" style={{minHeight: '1em'}} />
        </Box>
      </Box>
    );
  }

  const count = enrichedEvents.length;

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
        <Subtitle2>Recent updates</Subtitle2>
        <Caption color={Colors.textLighter()}>
          {count === 100
            ? 'Last 100 updates'
            : count === 0
              ? 'No materialization events found'
              : count === 1
                ? 'Showing one update'
                : `Showing all ${count} updates`}
        </Caption>
      </Box>
      <Box border="all" padding={6 as any} style={{height: 36, overflow: 'hidden'}}>
        <div {...containerProps} style={{width: '100%', height: 24, position: 'relative'}}>
          {batchedEvents.map((batch) => {
            const [firstRun] = batch.runs;
            if (!firstRun) {
              return null;
            }

            // Compute batch status flags
            const hasFailedMaterializations = batch.runs.some(
              (e) =>
                e.__typename === 'FailedToMaterializeEvent' &&
                e.materializationFailureType === 'FAILED',
            );
            const hasMaterializations = batch.runs.some(
              (e) => e.__typename === 'MaterializationEvent',
            );
            const hasSkippedMaterializations = batch.runs.some(
              (e) =>
                e.__typename === 'FailedToMaterializeEvent' &&
                e.materializationFailureType !== 'FAILED',
            );

            const timestamp = parseInt(firstRun.timestamp);
            const batchRange = batch.endTime - batch.startTime;
            const percent =
              batchRange > 0 ? (100 * (timestamp - batch.startTime)) / batchRange : 50;

            return (
              <TickWrapper
                key={firstRun.timestamp}
                style={{
                  left: `${batch.left}px`,
                  width: `${Math.max(batch.width, 12)}px`,
                }}
              >
                <InnerTick
                  key={batch.startTime}
                  style={{
                    // Make sure there's enough room to see the last tick.
                    left: `min(calc(100% - ${INNER_TICK_WIDTH}px), ${percent}%)`,
                  }}
                  $hasError={hasFailedMaterializations}
                  $hasSuccess={hasMaterializations}
                  $hasSkipped={hasSkippedMaterializations}
                />
                <Popover
                  position="top"
                  interactionKind="hover"
                  content={
                    <div style={{width: 400}}>
                      <Box padding={{vertical: 8, horizontal: 12}} border="bottom">
                        <Subtitle2>Updates</Subtitle2>
                      </Box>
                      <Box style={{maxHeight: '300px', overflowY: 'auto'}}>
                        {[...batch.runs]
                          .sort((a, b) => parseInt(b.timestamp) - parseInt(a.timestamp))
                          .map((event, index) => (
                            <AssetUpdate
                              assetKey={assetKey}
                              event={event}
                              key={event.timestamp}
                              last={index === batch.runs.length - 1}
                            />
                          ))}
                      </Box>
                    </div>
                  }
                >
                  <Tick
                    $hasError={hasFailedMaterializations}
                    $hasSuccess={hasMaterializations}
                    $hasSkipped={hasSkippedMaterializations}
                  >
                    <TickText>{batch.runs.length}</TickText>
                  </Tick>
                </Popover>
              </TickWrapper>
            );
          })}
          <TickLines />
        </div>
      </Box>
      <Box padding={{top: 4}} flex={{justifyContent: 'space-between'}}>
        <Caption color={Colors.textLighter()}>
          {formatDateTime(new Date(startTimestamp), {})}
        </Caption>
        <Caption color={Colors.textLighter()}>{formatDateTime(new Date(endTimestamp), {})}</Caption>
      </Box>
    </Box>
  );
};

const AssetUpdate = ({
  assetKey,
  event,
  last,
}: {
  assetKey: AssetKey;
  event: AssetEventType;
  last: boolean;
}) => {
  const run = event?.runOrError.__typename === 'Run' ? event.runOrError : null;
  const icon = () => {
    switch (event.__typename) {
      case 'MaterializationEvent':
        return <Icon name="run_success" color={Colors.accentGreen()} />;
      case 'ObservationEvent':
        return <Icon name="observation" color={Colors.accentGreen()} />;
      case 'FailedToMaterializeEvent':
        return event.materializationFailureType === 'FAILED' ? (
          <Icon name="run_failed" color={Colors.accentRed()} />
        ) : (
          <Icon name="status" color={Colors.accentGray()} />
        );
    }
  };

  const label = () => {
    switch (event.__typename) {
      case 'MaterializationEvent':
        return 'Materialized at';
      case 'ObservationEvent':
        return 'Observed at';
      case 'FailedToMaterializeEvent':
        return 'Failed to materialize at';
    }
  };

  return (
    <Box
      padding={{vertical: 8, horizontal: 12}}
      border={last ? null : 'bottom'}
      flex={{gap: 4, wrap: 'wrap'}}
      style={{fontSize: 12}}
    >
      <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
        {icon()}
        {label()}
        <Link
          to={assetDetailsPathForKey(assetKey, {
            view: 'events',
            time: event.timestamp,
          })}
        >
          <Caption>
            <Timestamp timestamp={{ms: Number(event.timestamp)}} />
          </Caption>
        </Link>
      </Box>
      <div>
        {event && run ? (
          <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
            <div>in run</div>
            <AssetRunLink
              runId={run.id}
              assetKey={assetKey}
              event={{stepKey: event.stepKey, timestamp: event.timestamp}}
            >
              <CaptionMono>{titleForRun(run)}</CaptionMono>
            </AssetRunLink>
          </Box>
        ) : event && isRunlessEvent(event) ? (
          <RunlessEventTag tags={event.tags} />
        ) : undefined}
      </div>
    </Box>
  );
};

const Tick = styled.div<{
  $hasError: boolean;
  $hasSuccess: boolean;
  $hasSkipped: boolean;
}>`
  position: absolute;
  width: 100%;
  top: 0;
  bottom: 0;
  overflow: hidden;
  background-color: transparent;
  cursor: pointer;
  border-radius: 2px;
  &:hover {
    background: ${({$hasError, $hasSuccess, $hasSkipped}) => {
      if ($hasError && $hasSuccess) {
        return `linear-gradient(90deg, ${Colors.accentRed()} 50%, ${Colors.accentGreen()} 50%)`;
      }
      if ($hasError) {
        return Colors.accentRed();
      }
      if ($hasSuccess) {
        return Colors.accentGreen();
      }
      if ($hasSkipped) {
        return Colors.accentGray();
      }
      return Colors.accentGreen();
    }};
  }
`;

const TickText = styled.div`
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  bottom: 0;
  display: grid;
  place-content: center;
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  color: transparent;
  background: none;
  user-select: none;
  &:hover {
    user-select: initial;
    color: ${Colors.accentReversed()};
  }
`;

const TickWrapper = styled.div`
  position: absolute;
  height: 24px;
  * {
    height: 24px;
  }
`;

const InnerTick = styled.div<{
  $hasError: boolean;
  $hasSuccess: boolean;
  $hasSkipped: boolean;
}>`
  width: 8px;
  top: 0;
  bottom: 0;
  position: absolute;
  pointer-events: none;
  border-radius: 1px;
  background: ${({$hasError, $hasSuccess, $hasSkipped}) => {
    if ($hasError && $hasSuccess) {
      return `linear-gradient(90deg, ${Colors.accentRed()} 50%, ${Colors.accentGreen()} 50%)`;
    }
    if ($hasError) {
      return Colors.accentRed();
    }
    if ($hasSuccess) {
      return Colors.accentGreen();
    }
    if ($hasSkipped) {
      return Colors.accentGray();
    }
    return Colors.accentGreen();
  }};
`;

const TickLines = styled.div`
  pointer-events: none;
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6px;
  top: -6px;
  background: repeating-linear-gradient(
    to right,
    ${Colors.keylineDefault} 0,
    ${Colors.keylineDefault} 2px,
    /* color and width of the line */ transparent 2px,
    transparent 5% /* spacing between lines */
  );
`;

const ONE_DAY = 24 * 60 * 60 * 1000;

function getTimelineBounds(sortedMaterializations: {timestamp: string}[]): [number, number] {
  if (!sortedMaterializations.length) {
    const nowUnix = Math.floor(Date.now());
    return [nowUnix - 7 * ONE_DAY, nowUnix];
  }

  const endTimestamp = parseInt(
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    sortedMaterializations[sortedMaterializations.length - 1]!.timestamp,
  );
  const startTimestamp = Math.min(
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    parseInt(sortedMaterializations[0]!.timestamp),
    endTimestamp - 100,
  );
  return [startTimestamp, endTimestamp];
}
