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
import {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {RunlessEventTag} from './RunlessEventTag';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {isRunlessEvent} from './isRunlessEvent';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {Timestamp} from '../app/time/Timestamp';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {TimestampMetadataEntry} from '../graphql/types';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const INNER_TICK_WIDTH = 4;
const MIN_TICK_WIDTH = 5;
const BUCKETS = 50;

type MaterializationType = ReturnType<typeof useRecentAssetEvents>['materializations'][0];
type ObservationType = ReturnType<typeof useRecentAssetEvents>['observations'][0];
type Props = {
  assetKey: AssetKey;
  materializations?: MaterializationType[];
  observations?: ObservationType[];
  loading: boolean;
};

export const RecentUpdatesTimeline = ({
  assetKey,
  observations,
  materializations,
  loading,
}: Props) => {
  const {containerProps, viewport} = useViewport();
  const widthAvailablePerTick = viewport.width / BUCKETS;

  const tickWidth = Math.max(widthAvailablePerTick, MIN_TICK_WIDTH);

  const buckets = Math.floor(viewport.width / tickWidth);

  const sortedMaterializations = useMemo(() => {
    if (!materializations && observations) {
      const seenTimestamps = new Set();
      return observations
        .map((obs) => {
          const lastUpdated = obs.metadataEntries.find(
            (entry) =>
              entry.__typename === 'TimestampMetadataEntry' &&
              entry.label === 'dagster/last_updated_timestamp',
          );
          const ts = (lastUpdated as TimestampMetadataEntry).timestamp;

          if (!seenTimestamps.has(ts)) {
            seenTimestamps.add(ts);
            return {
              ...obs,
              timestamp: `${ts}`,
              obsTimestamp: obs.timestamp,
            };
          }
          return null;
        })
        .filter((o) => o) as ObservationType[];
    }
    return [...(materializations ?? [])].sort(
      (a, b) => parseInt(a.timestamp) - parseInt(b.timestamp),
    );
  }, [materializations, observations]);

  const endTimestamp = parseInt(
    sortedMaterializations[sortedMaterializations.length - 1]?.timestamp ?? '0',
  );
  const startTimestamp = Math.min(
    parseInt(sortedMaterializations[0]?.timestamp ?? '0'),
    endTimestamp - 100,
  );
  const timeRange = endTimestamp - startTimestamp;
  const bucketTimeRange = timeRange / buckets;

  const bucketedMaterializations = useMemo(() => {
    if (!viewport.width) {
      return [];
    }
    const bucketsArr: Array<{
      start: number;
      end: number;
      materializations: (MaterializationType | ObservationType)[];
    }> = new Array(buckets);

    sortedMaterializations.forEach((materialization) => {
      const bucketIndex = Math.min(
        Math.floor((parseInt(materialization.timestamp) - startTimestamp) / bucketTimeRange),
        buckets - 1,
      );
      bucketsArr[bucketIndex] = bucketsArr[bucketIndex] || {
        start: bucketIndex,
        end: bucketIndex + 1,
        materializations: [],
      };
      bucketsArr[bucketIndex]!.materializations.push(materialization);
    });

    return bucketsArr;
  }, [viewport.width, buckets, sortedMaterializations, startTimestamp, bucketTimeRange]);

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

  const count = materializations?.length ?? 0;

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
            return (
              <TickWrapper
                key={bucket.start}
                style={{
                  left: (100 * bucket.start) / buckets + '%',
                  width: (100 * width) / buckets + '%',
                }}
              >
                {bucket.materializations.map(({timestamp}) => {
                  const bucketStartTime = startTimestamp + bucket.start * bucketTimeRange;
                  const bucketEndTimestamp = startTimestamp + bucket.end * bucketTimeRange;
                  const bucketRange = bucketEndTimestamp - bucketStartTime;
                  const percent = (100 * (parseInt(timestamp) - bucketStartTime)) / bucketRange;

                  return (
                    <InnerTick
                      key={timestamp}
                      style={{
                        // Make sure there's enough room to see the last tick.
                        left: `min(calc(100% - ${INNER_TICK_WIDTH}px), ${percent}%`,
                      }}
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
                        {bucket.materializations
                          .sort((a, b) => parseInt(b.timestamp) - parseInt(a.timestamp))
                          .map((materialization, index) => (
                            <AssetUpdate assetKey={assetKey} event={materialization} key={index} />
                          ))}
                      </div>
                    </Box>
                  }
                >
                  <>
                    <Tick>
                      <TickText>{bucket.materializations.length}</TickText>
                    </Tick>
                  </>
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
}: {
  assetKey: AssetKey;
  event: MaterializationType | ObservationType;
}) => {
  const run = event?.runOrError.__typename === 'Run' ? event.runOrError : null;
  return (
    <Box padding={4} border="bottom" flex={{justifyContent: 'space-between', gap: 8}}>
      <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
        {event.__typename === 'MaterializationEvent' ? (
          <Icon name="materialization" />
        ) : (
          <Icon name="observation" />
        )}
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

const Tick = styled.div`
  position: absolute;
  width 100%;
  top: 0;
  bottom: 0;
  overflow: hidden;
  background-color: transparent;
  cursor: pointer;
  border-radius: 2px;
  &:hover {
    background-color: ${Colors.accentGreenHover()};
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
  color: transparent;
  background: none;
  user-select: none;
  &:hover {
    user-select: initial;
    color: ${Colors.textLight()};
  }
`;

const TickWrapper = styled.div`
  position: absolute;
  height: 20px;
  * {
    height: 20px;
  }
`;

const InnerTick = styled.div`
  width: ${INNER_TICK_WIDTH}px;
  background-color: ${Colors.accentGreen()};
  top: 0;
  bottom: 0;
  position: absolute;
  pointer-events: none;
  border-radius: 1px;
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
