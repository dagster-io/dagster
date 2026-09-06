import {
  Box,
  Button,
  Colors,
  Heading,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Skeleton,
  Text,
  useViewport,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useCallback, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {RunlessEventTag} from './RunlessEventTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import styles from './css/RecentUpdatesTimeline.module.css';
import {isRunlessEvent} from './isRunlessEvent';
import {AssetKey} from './types';
import {
  RecentAssetEventsQuery,
  RecentAssetEventsQueryVariables,
} from './types/useRecentAssetEvents.types';
import {AssetEventFragment, RECENT_ASSET_EVENTS_QUERY} from './useRecentAssetEvents';
import {useRefreshAtInterval} from '../app/QueryRefresh';
import {Timestamp} from '../app/time/Timestamp';
import {usePrefixedCacheKey} from '../app/usePrefixedCacheKey';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {titleForRun} from '../runs/RunUtils';
import {batchRunsForTimeline} from '../runs/batchRunsForTimeline';
import {useCursorAccumulatedQuery} from '../runs/useCursorAccumulatedQuery';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const EVENT_TYPE_FILTER_KEY = 'asset-timeline-event-type-filter';
const TIME_RANGE_FILTER_KEY = 'asset-timeline-time-range-filter';

type EventTypeFilter = 'all' | 'materializations' | 'observations';
export type TimeRangeFilter = '24h' | '48h' | '3d' | '7d' | '30d';

const ONE_HOUR = 60 * 60 * 1000;
const ONE_DAY = 24 * ONE_HOUR;

const TIME_RANGE_MS: Record<TimeRangeFilter, number> = {
  '24h': 24 * ONE_HOUR,
  '48h': 48 * ONE_HOUR,
  '3d': 3 * ONE_DAY,
  '7d': 7 * ONE_DAY,
  '30d': 30 * ONE_DAY,
};

const TIME_RANGE_OPTIONS = Object.keys(TIME_RANGE_MS) as TimeRangeFilter[];

const TIME_RANGE_LABELS: Record<TimeRangeFilter, string> = {
  '24h': 'Last 24 hours',
  '48h': 'Last 48 hours',
  '3d': 'Last 3 days',
  '7d': 'Last 7 days',
  '30d': 'Last 30 days',
};

const EVENT_FILTER_LABELS: Record<EventTypeFilter, string> = {
  all: 'Show events',
  materializations: 'Show materialization events',
  observations: 'Show observation events',
};

const RIGHT_PADDING_PX = 12;
const MIN_MULTIPLE_WIDTH = 20;
const LABEL_HEIGHT_PX = 18;
const TRACK_HEIGHT_PX = 32;

type AssetEventType = AssetEventFragment;

const FETCH_LIMIT = 100;

function useTimeWindowAssetEvents(assetKey: AssetKey, timeRange: TimeRangeFilter, now: number) {
  const afterTimestamp = useMemo(() => String(now - TIME_RANGE_MS[timeRange]), [now, timeRange]);

  const variables = useMemo(
    () => ({
      limit: FETCH_LIMIT,
      assetKey: {path: assetKey.path},
      after: afterTimestamp,
      eventTypeSelectors: [
        AssetEventHistoryEventTypeSelector.MATERIALIZATION,
        AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
        AssetEventHistoryEventTypeSelector.OBSERVATION,
      ],
    }),
    [assetKey, afterTimestamp],
  );

  const getResult = useCallback((data: RecentAssetEventsQuery) => {
    const asset = data.assetOrError.__typename === 'Asset' ? data.assetOrError : null;
    const history = asset?.assetEventHistory;
    const results = (history?.results ?? []) as AssetEventType[];
    const cursor = history?.cursor ?? undefined;
    return {
      data: results,
      hasMore: results.length === FETCH_LIMIT,
      cursor,
      error: undefined,
    };
  }, []);

  const {fetched} = useCursorAccumulatedQuery<
    RecentAssetEventsQuery,
    RecentAssetEventsQueryVariables,
    AssetEventType
  >({
    query: RECENT_ASSET_EVENTS_QUERY,
    variables,
    getResult,
  });

  return {events: fetched};
}

export type RecentUpdatesTimelineViewProps = {
  assetKey: AssetKey;
  // null = loading; [] = empty; [...] = loaded events
  events: AssetEventType[] | null;
  timeRange: TimeRangeFilter;
  setTimeRange: (range: TimeRangeFilter) => void;
  eventFilter: EventTypeFilter;
  setEventFilter: (filter: EventTypeFilter) => void;
  // Override the current time for the timeline's right edge. Defaults to Date.now().
  // Useful in stories/tests where events have hardcoded timestamps in the past.
  now?: number;
};

export const RecentUpdatesTimelineView = ({
  assetKey,
  events,
  timeRange,
  setTimeRange,
  eventFilter,
  setEventFilter,
  now: nowProp,
}: RecentUpdatesTimelineViewProps) => {
  const loading = events === null;
  const {containerProps, viewport} = useViewport();

  const enrichedEvents = useMemo(() => enrichObservationTimestamps(events ?? []), [events]);

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
    if (eventFilter === 'materializations') {
      return {
        hasBothEventTypes: true,
        displayedEvents: enrichedEvents.filter((e) => e.__typename !== 'ObservationEvent'),
      };
    }
    return {hasBothEventTypes: true, displayedEvents: enrichedEvents};
  }, [enrichedEvents, eventFilter]);

  const [startTimestamp, endTimestamp] = useMemo(() => {
    const now = nowProp ?? Date.now();
    return [now - TIME_RANGE_MS[timeRange], now];
  }, [timeRange, nowProp]);

  const batchedEvents = useMemo(() => {
    if (!viewport.width || !displayedEvents.length) {
      return [];
    }

    const eventsAsRuns = displayedEvents.map((event) => ({
      ...event,
      startTime: parseInt(event.timestamp),
      endTime: parseInt(event.timestamp) + 1,
    }));

    return batchRunsForTimeline({
      runs: eventsAsRuns,
      start: startTimestamp,
      end: endTimestamp,
      width: viewport.width - RIGHT_PADDING_PX,
      minChunkWidth: 1,
      minMultipleWidth: MIN_MULTIPLE_WIDTH,
    });
  }, [viewport.width, displayedEvents, startTimestamp, endTimestamp]);

  // Gridlines aligned to real clock boundaries: hourly for the 24h/48h windows,
  // daily for the longer ones.
  const axisTicks = useMemo(() => {
    const totalRange = endTimestamp - startTimestamp;
    if (!viewport.width || totalRange <= 0) {
      return [];
    }
    const granularity: AxisTickGranularity =
      timeRange === '24h' || timeRange === '48h' ? 'hour' : 'day';
    const availableWidth = viewport.width - RIGHT_PADDING_PX;
    return getAxisTickTimestamps(startTimestamp, endTimestamp, granularity).map((ts) => ({
      ts,
      left: ((ts - startTimestamp) / totalRange) * availableWidth,
    }));
  }, [viewport.width, startTimestamp, endTimestamp, timeRange]);

  const formatDateTime = useFormatDateTime();

  const headerRow = (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
      <Heading size={14} weight={600}>
        Asset history
      </Heading>
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Popover
          placement="bottom-end"
          content={
            <Menu>
              {TIME_RANGE_OPTIONS.map((range) => (
                <MenuItem
                  key={range}
                  text={TIME_RANGE_LABELS[range]}
                  onClick={() => setTimeRange(range)}
                />
              ))}
            </Menu>
          }
        >
          <Button icon={<Icon name="calendar" />} rightIcon={<Icon name="arrow_drop_down" />}>
            {TIME_RANGE_LABELS[timeRange]}
          </Button>
        </Popover>
        {hasBothEventTypes && (
          <Popover
            placement="bottom-end"
            content={
              <Menu>
                <MenuItem text={EVENT_FILTER_LABELS.all} onClick={() => setEventFilter('all')} />
                <MenuItem
                  text={EVENT_FILTER_LABELS.materializations}
                  onClick={() => setEventFilter('materializations')}
                />
                <MenuItem
                  text={EVENT_FILTER_LABELS.observations}
                  onClick={() => setEventFilter('observations')}
                />
              </Menu>
            }
          >
            <Button icon={<Icon name="filter_alt" />} rightIcon={<Icon name="arrow_drop_down" />}>
              {EVENT_FILTER_LABELS[eventFilter]}
            </Button>
          </Popover>
        )}
      </Box>
    </Box>
  );

  if (loading) {
    return (
      <Box flex={{direction: 'column', gap: 4}}>
        {headerRow}
        <div style={{height: LABEL_HEIGHT_PX}} />

        <Skeleton $width="100%" $height={TRACK_HEIGHT_PX} />
        <Box padding={{top: 4}} flex={{justifyContent: 'space-between'}}>
          <Skeleton $width={70} $height="1em" style={{minHeight: '1em'}} />
          <Skeleton $width={70} $height="1em" style={{minHeight: '1em'}} />
        </Box>
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      {headerRow}
      <div {...containerProps} className={styles.timelineContainer}>
        <div className={styles.timelineInner}>
          <Box border="all" className={styles.track}>
            {axisTicks.map((tick) => (
              <div key={tick.ts} className={styles.axisTick} style={{left: `${tick.left}px`}} />
            ))}
          </Box>
          {batchedEvents.map((batch) => {
            const [firstRun] = batch.runs;
            if (!firstRun) {
              return null;
            }
            if (batch.left < MIN_MULTIPLE_WIDTH / 2) {
              return null;
            }

            const {hasError, hasSuccess, hasSkipped} = getBatchStatus(batch.runs);
            const colorClass = getTickColorClass(hasError, hasSuccess, hasSkipped);

            const popoverContent = (
              <div style={{width: 400}}>
                <Box padding={{vertical: 8, horizontal: 12}} border="bottom">
                  <Heading size={14} weight={600}>
                    Updates
                  </Heading>
                </Box>
                <div style={{maxHeight: '300px', overflowY: 'auto'}}>
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
                </div>
              </div>
            );

            return (
              <div
                key={firstRun.timestamp}
                className={styles.tickWrapper}
                style={{left: `${batch.left}px`, width: `${MIN_MULTIPLE_WIDTH}px`}}
              >
                <Popover position="bottom" interactionKind="hover" content={popoverContent}>
                  <div className={styles.tickOuter}>
                    <div className={styles.tickLabel}>
                      {batch.runs.length === 1 ? (
                        <Icon
                          name={getSingleTickIcon(firstRun)}
                          color={getTickAccentColor(hasError, hasSkipped)}
                          size={16}
                        />
                      ) : (
                        <Text size={12} style={{color: getTickTextColor(hasError, hasSkipped)}}>
                          {batch.runs.length}
                        </Text>
                      )}
                    </div>
                    <div className={clsx(styles.innerTick, colorClass)} />
                  </div>
                </Popover>
              </div>
            );
          })}
        </div>
      </div>
      <Box padding={{top: 4}} flex={{justifyContent: 'space-between'}}>
        <Text size={12} color="textLighter">
          {formatDateTime(new Date(startTimestamp), {})}
        </Text>
        <Text size={12} color="textLighter">
          {formatDateTime(new Date(endTimestamp), {})}
        </Text>
      </Box>
    </Box>
  );
};

export const RecentUpdatesTimeline = ({assetKey}: {assetKey: AssetKey}) => {
  const storageKey = usePrefixedCacheKey(EVENT_TYPE_FILTER_KEY);
  const timeRangeStorageKey = usePrefixedCacheKey(TIME_RANGE_FILTER_KEY);

  const [now, setNow] = useState(Date.now());
  useRefreshAtInterval({
    refresh: useCallback(() => setNow(Date.now()), [setNow]),
    intervalMs: 120 * 1000,
  });
  const [eventFilter, setEventFilter] = useStateWithStorage<EventTypeFilter>(storageKey, (json) => {
    if (json === 'observations') {
      return 'observations';
    }
    if (json === 'all') {
      return 'all';
    }
    return 'materializations';
  });
  const [timeRange, setTimeRange] = useStateWithStorage<TimeRangeFilter>(
    timeRangeStorageKey,
    (json) =>
      (TIME_RANGE_OPTIONS as string[]).includes(json as string) ? (json as TimeRangeFilter) : '7d',
  );

  const {events} = useTimeWindowAssetEvents(assetKey, timeRange, now);

  return (
    <RecentUpdatesTimelineView
      assetKey={assetKey}
      events={events}
      timeRange={timeRange}
      setTimeRange={setTimeRange}
      eventFilter={eventFilter}
      setEventFilter={setEventFilter}
      now={now}
    />
  );
};

// Observations may carry a `dagster/last_updated_timestamp` metadata entry that represents
// when the underlying data was last updated (vs. when the observation itself was recorded).
// This function re-timestamps observations using that value when present, and deduplicates
// observations that resolve to the same effective timestamp.
function enrichObservationTimestamps(events: AssetEventType[]): AssetEventType[] {
  const seenTimestamps = new Set<number>();
  return events
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

      // The metadata timestamp is in seconds; event.timestamp is in milliseconds.
      const ts = lastUpdated?.timestamp ? lastUpdated.timestamp * 1000 : parseInt(event.timestamp);

      if (seenTimestamps.has(ts)) {
        return null;
      }
      seenTimestamps.add(ts);
      return {...event, timestamp: `${ts}`};
    })
    .filter((e): e is AssetEventType => e !== null)
    .sort((a, b) => parseInt(a.timestamp) - parseInt(b.timestamp));
}

type AxisTickGranularity = 'hour' | 'day';

// Produce timestamps aligned to local hour or day boundaries within [start, end].
// These drive the timeline's background gridlines. Using Date setters (rather than
// fixed ms steps) keeps ticks pinned to real clock boundaries across DST shifts.
function getAxisTickTimestamps(
  start: number,
  end: number,
  granularity: AxisTickGranularity,
): number[] {
  const ticks: number[] = [];
  const cursor = new Date(start);

  if (granularity === 'hour') {
    cursor.setMinutes(0, 0, 0);
    if (cursor.getTime() < start) {
      cursor.setHours(cursor.getHours() + 1);
    }
    while (cursor.getTime() <= end) {
      ticks.push(cursor.getTime());
      cursor.setHours(cursor.getHours() + 1);
    }
  } else {
    cursor.setHours(0, 0, 0, 0);
    if (cursor.getTime() < start) {
      cursor.setDate(cursor.getDate() + 1);
    }
    while (cursor.getTime() <= end) {
      ticks.push(cursor.getTime());
      cursor.setDate(cursor.getDate() + 1);
    }
  }

  return ticks;
}

// Returns the status flags for a batch of events, used for coloring tick marks and labels.
function getBatchStatus(runs: AssetEventType[]) {
  return {
    hasError: runs.some(
      (e) =>
        e.__typename === 'FailedToMaterializeEvent' && e.materializationFailureType === 'FAILED',
    ),
    hasSuccess: runs.some((e) => e.__typename === 'MaterializationEvent'),
    hasSkipped: runs.some(
      (e) =>
        e.__typename === 'FailedToMaterializeEvent' && e.materializationFailureType !== 'FAILED',
    ),
  };
}

function getSingleTickIcon(
  event: AssetEventType,
): 'materialization' | 'error_outline' | 'observation' {
  switch (event.__typename) {
    case 'MaterializationEvent':
      return 'materialization';
    case 'FailedToMaterializeEvent':
      return 'error_outline';
    case 'ObservationEvent':
      return 'observation';
    default:
      return 'observation';
  }
}

function getTickAccentColor(hasError: boolean, hasSkipped: boolean): string {
  if (hasError) {
    return Colors.accentRed();
  }
  if (hasSkipped) {
    return Colors.accentGray();
  }
  return Colors.accentGreen();
}

function getTickTextColor(hasError: boolean, hasSkipped: boolean): string {
  if (hasError) {
    return Colors.textRed();
  }
  if (hasSkipped) {
    return Colors.textLighter();
  }
  return Colors.textGreen();
}

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
      default:
        return null;
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
      default:
        return null;
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
          <Text size={12}>
            <Timestamp timestamp={{ms: Number(event.timestamp)}} />
          </Text>
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
              <Text size={12} family="mono">
                {titleForRun(run)}
              </Text>
            </AssetRunLink>
          </Box>
        ) : event && isRunlessEvent(event) ? (
          <RunlessEventTag tags={event.tags} />
        ) : undefined}
      </div>
    </Box>
  );
};
