import {
  Box,
  ButtonLink,
  Caption,
  CaptionMono,
  Colors,
  Icon,
  Popover,
  Skeleton,
  Subtitle2,
  useViewport,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {memo, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {RunlessEventTag} from './RunlessEventTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import styles from './css/RecentUpdatesTimeline.module.css';
import {isRunlessEvent} from './isRunlessEvent';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {Timestamp} from '../app/time/Timestamp';
import {usePrefixedCacheKey} from '../app/usePrefixedCacheKey';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {titleForRun} from '../runs/RunUtils';
import {batchRunsForTimeline} from '../runs/batchRunsForTimeline';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const EVENT_TYPE_FILTER_KEY = 'asset-timeline-event-type-filter';
type EventTypeFilter = 'materializations' | 'observations';

const INNER_TICK_WIDTH = 4;
const RIGHT_PADDING_PX = 12;

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

  const storageKey = usePrefixedCacheKey(EVENT_TYPE_FILTER_KEY);
  const [eventFilter, setEventFilter] = useStateWithStorage<EventTypeFilter>(storageKey, (json) =>
    json === 'observations' ? 'observations' : 'materializations',
  );

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

  const {hasBothEventTypes, displayedEvents} = useMemo(() => {
    const hasBoth =
      enrichedEvents.some((e) => e.__typename === 'ObservationEvent') &&
      enrichedEvents.some(
        (e) =>
          e.__typename === 'MaterializationEvent' || e.__typename === 'FailedToMaterializeEvent',
      );

    if (!hasBoth) {
      return {hasBothEventTypes: false, displayedEvents: enrichedEvents};
    }
    if (eventFilter === 'observations') {
      return {
        hasBothEventTypes: true,
        displayedEvents: enrichedEvents.filter((e) => e.__typename === 'ObservationEvent'),
      };
    }
    return {
      hasBothEventTypes: true,
      displayedEvents: enrichedEvents.filter((e) => e.__typename !== 'ObservationEvent'),
    };
  }, [enrichedEvents, eventFilter]);

  // Bounds are computed from all events so the timeline range stays stable when switching filters.
  const [startTimestamp, endTimestamp] = getTimelineBounds(enrichedEvents);

  const batchedEvents = useMemo(() => {
    if (!viewport.width || !displayedEvents.length) {
      return [];
    }

    // Convert events to runs with synthetic 1ms duration
    const eventsAsRuns = displayedEvents.map((event) => ({
      ...event,
      startTime: parseInt(event.timestamp),
      endTime: parseInt(event.timestamp) + 1,
    }));

    // Use shared batching logic
    return batchRunsForTimeline({
      runs: eventsAsRuns,
      start: startTimestamp,
      end: endTimestamp,
      width: viewport.width - RIGHT_PADDING_PX,
      minChunkWidth: 1, // INNER_TICK_WIDTH
      minMultipleWidth: 10,
    });
  }, [viewport.width, displayedEvents, startTimestamp, endTimestamp]);

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

  const totalCount = enrichedEvents.length;
  const count = displayedEvents.length;

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <Subtitle2>Recent updates</Subtitle2>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Caption color={Colors.textLighter()}>
            {totalCount === 100
              ? hasBothEventTypes && count < totalCount
                ? `Showing ${count} of last 100 updates`
                : 'Last 100 updates'
              : count === 0
                ? 'No events found'
                : count === 1
                  ? 'Showing one update'
                  : `Showing all ${count} updates`}
          </Caption>
          {hasBothEventTypes && (
            <Caption>
              <ButtonLink
                color={
                  eventFilter === 'materializations' ? Colors.textDefault() : Colors.textLighter()
                }
                underline="hover"
                style={{fontWeight: eventFilter === 'materializations' ? 600 : undefined}}
                onClick={() => setEventFilter('materializations')}
              >
                Materializations
              </ButtonLink>
              {' \u2022 '}
              <ButtonLink
                color={eventFilter === 'observations' ? Colors.textDefault() : Colors.textLighter()}
                underline="hover"
                style={{fontWeight: eventFilter === 'observations' ? 600 : undefined}}
                onClick={() => setEventFilter('observations')}
              >
                Observations
              </ButtonLink>
            </Caption>
          )}
        </Box>
      </Box>
      <Box border="all" style={{height: 36, overflow: 'hidden', padding: '6px 0'}}>
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

            const colorClass = getTickColorClass(
              hasFailedMaterializations,
              hasMaterializations,
              hasSkippedMaterializations,
            );

            const timestamp = parseInt(firstRun.timestamp);
            const batchRange = batch.endTime - batch.startTime;
            const percent =
              batchRange > 0 ? (100 * (timestamp - batch.startTime)) / batchRange : 50;

            return (
              <div
                key={firstRun.timestamp}
                className={styles.tickWrapper}
                style={{
                  left: `${batch.left}px`,
                  width: `${Math.max(batch.width, 12)}px`,
                }}
              >
                <div
                  key={batch.startTime}
                  className={clsx(styles.innerTick, colorClass)}
                  style={{
                    // Make sure there's enough room to see the last tick.
                    left: `min(calc(100% - ${INNER_TICK_WIDTH}px), ${percent}%)`,
                  }}
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
                  <div className={clsx(styles.tick, colorClass)}>
                    <div className={styles.tickText}>{batch.runs.length}</div>
                  </div>
                </Popover>
              </div>
            );
          })}
          <div className={styles.tickLines} />
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

function getTickColorClass(hasError: boolean, hasSuccess: boolean, hasSkipped: boolean) {
  if (hasError && hasSuccess) {
    return styles.mixed;
  }
  if (hasError) {
    return styles.error;
  }
  if (hasSkipped) {
    return styles.skipped;
  }
  return null;
}

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

const ONE_DAY = 24 * 60 * 60 * 1000;

function getTimelineBounds(sortedMaterializations: {timestamp: string}[]): [number, number] {
  const firstSorted = sortedMaterializations[0];
  const lastSorted = sortedMaterializations[sortedMaterializations.length - 1];

  if (!firstSorted || !lastSorted) {
    const nowUnix = Math.floor(Date.now());
    return [nowUnix - 7 * ONE_DAY, nowUnix];
  }

  const endTimestamp = parseInt(lastSorted.timestamp);
  const startTimestamp = parseInt(firstSorted.timestamp);

  return [startTimestamp, endTimestamp];
}
