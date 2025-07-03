import {
  Box,
  Caption,
  Colors,
  Icon,
  Popover,
  Skeleton,
  Subtitle2,
  Tag,
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
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const INNER_TICK_WIDTH = 4;
const MIN_TICK_WIDTH = 5;
const BUCKETS = 50;

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
  const widthAvailablePerTick = viewport.width / BUCKETS;

  const tickWidth = Math.max(widthAvailablePerTick, MIN_TICK_WIDTH);

  const buckets = Math.floor(viewport.width / tickWidth);

  const enrichedEvents = useMemo(() => {
    const seenTimestamps = new Set();
    return events
      ?.map((event) => {
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
      .filter((e) => e) as AssetEventType[];
  }, [events]);

  const sortedEvents = enrichedEvents?.sort(
    (a, b) => parseInt(a.timestamp) - parseInt(b.timestamp),
  );

  const [startTimestamp, endTimestamp] = getTimelineBounds(sortedEvents);
  const timeRange = endTimestamp - startTimestamp;
  const bucketTimeRange = timeRange / buckets;

  const bucketedMaterializations = useMemo(() => {
    if (!viewport.width) {
      return [];
    }
    const bucketsArr: Array<{
      start: number;
      end: number;
      events: AssetEventType[];
      hasFailedMaterializations: boolean;
      hasMaterializations: boolean;
    }> = new Array(buckets);

    sortedEvents?.forEach((e) => {
      const bucketIndex = Math.min(
        Math.floor((parseInt(e.timestamp) - startTimestamp) / bucketTimeRange),
        buckets - 1,
      );
      bucketsArr[bucketIndex] = bucketsArr[bucketIndex] || {
        start: bucketIndex,
        end: bucketIndex + 1,
        events: [],
        hasFailedMaterializations: false,
        hasMaterializations: false,
      };
      bucketsArr[bucketIndex]!.events.push(e);
      if (e.__typename === 'FailedToMaterializeEvent') {
        bucketsArr[bucketIndex]!.hasFailedMaterializations = true;
      } else {
        bucketsArr[bucketIndex]!.hasMaterializations = true;
      }
    });

    return bucketsArr;
  }, [viewport.width, buckets, sortedEvents, startTimestamp, bucketTimeRange]);

  const formatDateTime = useFormatDateTime();

  if (loading) {
    return (
      <Box flex={{direction: 'column', gap: 4}}>
        <Box flex={{direction: 'row'}}>
          <Subtitle2>Recent updates</Subtitle2>
        </Box>
        <Skeleton $width="100%" $height={32} />
        <Box padding={{top: 4}} flex={{justifyContent: 'space-between'}}>
          <Skeleton $width={70} $height="1em" style={{minHeight: '1em'}} />
          <Skeleton $width={70} $height="1em" style={{minHeight: '1em'}} />
        </Box>
      </Box>
    );
  }

  const count = sortedEvents?.length ?? 0;

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
      <Box border="all" padding={6 as any} style={{height: 32, overflow: 'hidden'}}>
        <div {...containerProps} style={{width: '100%', height: 20, position: 'relative'}}>
          {bucketedMaterializations.map((bucket) => {
            const width = bucket.end - bucket.start;
            const bucketStartTime = startTimestamp + bucket.start * bucketTimeRange;
            const bucketEndTimestamp = startTimestamp + bucket.end * bucketTimeRange;
            const bucketRange = bucketEndTimestamp - bucketStartTime;
            return (
              <div
                key={bucket.start}
                className={styles.tickWrapper}
                style={{
                  left: (100 * bucket.start) / buckets + '%',
                  width: (100 * width) / buckets + '%',
                }}
              >
                {bucket.events.map(({timestamp, __typename}) => {
                  const percent = (100 * (parseInt(timestamp) - bucketStartTime)) / bucketRange;

                  return (
                    <div
                      key={timestamp}
                      className={clsx(
                        styles.innerTick,
                        __typename !== 'FailedToMaterializeEvent' ? styles.success : styles.error,
                      )}
                      style={
                        {
                          // Make sure there's enough room to see the last tick.
                          left: `min(calc(100% - ${INNER_TICK_WIDTH}px), ${percent}%`,
                          '--inner-tick-width': `${INNER_TICK_WIDTH}px`,
                        } as React.CSSProperties
                      }
                    />
                  );
                })}
                <Popover
                  position="top"
                  interactionKind="hover"
                  content={
                    <Box flex={{direction: 'column', gap: 8}}>
                      <Box padding={8} border="bottom">
                        <Subtitle2>Updates</Subtitle2>
                      </Box>
                      <div style={{maxHeight: 'min(80vh, 300px)', overflow: 'scroll'}}>
                        {bucket.events
                          .sort((a, b) => parseInt(b.timestamp) - parseInt(a.timestamp))
                          .map((event, index) => (
                            <AssetUpdate assetKey={assetKey} event={event} key={index} />
                          ))}
                      </div>
                    </Box>
                  }
                >
                  <>
                    <div
                      className={clsx(
                        styles.tick,
                        bucket.hasFailedMaterializations &&
                          bucket.hasMaterializations &&
                          styles.hasErrorAndSuccess,
                        bucket.hasFailedMaterializations && styles.hasError,
                        bucket.hasMaterializations && styles.hasSuccess,
                      )}
                    >
                      <div className={styles.tickText}>{bucket.events.length}</div>
                    </div>
                  </>
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

const AssetUpdate = ({assetKey, event}: {assetKey: AssetKey; event: AssetEventType}) => {
  const run = event?.runOrError.__typename === 'Run' ? event.runOrError : null;
  const icon = useMemo(() => {
    switch (event.__typename) {
      case 'MaterializationEvent':
        return <Icon name="run_success" color={Colors.accentGreen()} size={16} />;
      case 'ObservationEvent':
        return <Icon name="observation" color={Colors.accentGreen()} size={16} />;
      case 'FailedToMaterializeEvent':
        return <Icon name="run_failed" color={Colors.accentRed()} size={16} />;
    }
  }, [event.__typename]);
  return (
    <Box padding={4} border="bottom" flex={{justifyContent: 'space-between', gap: 8}}>
      <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
        {icon}
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
          <Tag>
            <AssetRunLink
              runId={run.id}
              assetKey={assetKey}
              event={{stepKey: event.stepKey, timestamp: event.timestamp}}
            >
              <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
                <RunStatusWithStats runId={run.id} status={run.status} size={8} />
                {titleForRun(run)}
              </Box>
            </AssetRunLink>
          </Tag>
        ) : event && isRunlessEvent(event) ? (
          <RunlessEventTag tags={event.tags} />
        ) : undefined}
      </div>
    </Box>
  );
};

const ONE_DAY = 24 * 60 * 60 * 1000;

function getTimelineBounds(sortedMaterializations: {timestamp: string}[]): [number, number] {
  if (!sortedMaterializations.length) {
    const nowUnix = Math.floor(Date.now());
    return [nowUnix - 7 * ONE_DAY, nowUnix];
  }

  const endTimestamp = parseInt(
    sortedMaterializations[sortedMaterializations.length - 1]!.timestamp,
  );
  const startTimestamp = Math.min(
    parseInt(sortedMaterializations[0]!.timestamp),
    endTimestamp - 100,
  );
  return [startTimestamp, endTimestamp];
}
