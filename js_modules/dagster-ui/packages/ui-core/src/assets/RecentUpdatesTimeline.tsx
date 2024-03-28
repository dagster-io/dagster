import {
  Box,
  Caption,
  Colors,
  Icon,
  Popover,
  Spinner,
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
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const MIN_TICK_WIDTH = 5;
const BUCKETS = 100;

export const RecentUpdatesTimeline = ({
  assetKey,
  materializations,
  loading,
}: {
  assetKey: AssetKey;
  materializations: ReturnType<typeof useRecentAssetEvents>['materializations'];
  loading: boolean;
}) => {
  const {containerProps, viewport} = useViewport();
  const widthAvailablePerTick = viewport.width / BUCKETS;

  const tickWidth = Math.max(widthAvailablePerTick, MIN_TICK_WIDTH);

  const buckets = Math.floor(viewport.width / tickWidth);

  const endTimestamp = parseInt(materializations[0]?.timestamp ?? '0');
  const startTimestamp = parseInt(materializations[materializations.length - 1]?.timestamp ?? '0');
  const range = endTimestamp - startTimestamp;

  const bucketedMaterializations = useMemo(() => {
    if (!viewport.width) {
      return [];
    }
    const firstPassBucketsArray: Array<{
      number: number;
      materializations: typeof materializations;
    }> = new Array(buckets);

    materializations.forEach((materialization) => {
      const bucketNumber = Math.floor(
        ((parseInt(materialization.timestamp) - startTimestamp) / range) * buckets,
      );
      firstPassBucketsArray[bucketNumber] = firstPassBucketsArray[bucketNumber] || {
        number: bucketNumber,
        materializations: [] as typeof materializations,
      };
      firstPassBucketsArray[bucketNumber]!.materializations.push(materialization);
    });

    const secondPassBucketsArray: Array<{
      start: number;
      end: number;
      materializations: typeof materializations;
    }> = [];

    firstPassBucketsArray.forEach((bucket) => {
      const lastBucket = secondPassBucketsArray[secondPassBucketsArray.length - 1];
      if (!lastBucket || lastBucket.end !== bucket.number - 1) {
        secondPassBucketsArray.push({
          start: bucket.number,
          end: bucket.number,
          materializations: bucket.materializations,
        });
      } else {
        lastBucket.end = bucket.number;
        lastBucket.materializations = [...lastBucket.materializations, ...bucket.materializations];
      }
    });

    return secondPassBucketsArray;
  }, [viewport.width, buckets, materializations, startTimestamp, range]);

  const formatDateTime = useFormatDateTime();

  if (loading) {
    return (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Subtitle2>Recent updates</Subtitle2>
        <Spinner purpose="body-text" />
      </Box>
    );
  }

  if (!materializations.length) {
    return (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Subtitle2>Recent updates</Subtitle2>
        <Caption color={Colors.textLight()}>No materialization events found</Caption>
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
        <Subtitle2>Recent updates</Subtitle2>
        <Caption color={Colors.textLighter()}>
          {materializations.length === 100
            ? 'Last 100 updates'
            : `Showing all ${materializations.length} updates`}
        </Caption>
      </Box>
      <Box border="all" padding={6 as any} style={{height: 32}}>
        <div {...containerProps} style={{width: '100%', height: 20, position: 'relative'}}>
          {bucketedMaterializations.map((bucket) => {
            const width = Math.max(bucket.end - bucket.start, 1);
            return (
              <>
                <TickWrapper
                  key={bucket.start}
                  style={{
                    left: `${(bucket.start * 100) / 101}%`,
                    width: `${(width * 100) / 101}%`,
                  }}
                >
                  <Popover
                    content={
                      <Box flex={{direction: 'column', gap: 8}}>
                        <Box padding={8} border="bottom">
                          <Subtitle2>Materializations</Subtitle2>
                        </Box>
                        <div style={{maxHeight: 'min(80vh, 300px)', overflow: 'scroll'}}>
                          {bucket.materializations
                            .sort((a, b) => parseInt(b.timestamp) - parseInt(a.timestamp))
                            .map((materialization, index) => (
                              <AssetUpdate
                                assetKey={assetKey}
                                event={materialization}
                                key={index}
                              />
                            ))}
                        </div>
                      </Box>
                    }
                  >
                    <>
                      <Tick>
                        {bucket.materializations.map(({timestamp}) => {
                          const bucketRange = Math.max(bucket.end - bucket.start, 1);
                          const left = (100 * (parseInt(timestamp) - startTimestamp)) / range;
                          const leftInner = (100 * (left - bucket.start)) / bucketRange;
                          return (
                            <InnerTick
                              key={timestamp}
                              style={{
                                left: `${leftInner}%`,
                              }}
                            />
                          );
                        })}
                        <TickText>
                          {bucket.materializations.length > 1
                            ? bucket.materializations.length
                            : null}
                        </TickText>
                      </Tick>
                    </>
                  </Popover>
                </TickWrapper>
              </>
            );
          })}
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
  event: ReturnType<typeof useRecentAssetEvents>['materializations'][0];
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
  background-color: ${Colors.backgroundGreen()};
  cursor: pointer;
  border-radius: 2px;

`;

const TickText = styled.div`
  display: grid;
  place-content: center;
  color: transparent;
  &:hover {
    background-color: ${Colors.accentGreenHover()};
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
  width: 1px;
  background-color: ${Colors.accentGreen()};
  top: 0;
  bottom: 0;
  position: absolute;
  opacity: 0.5;
  pointer-events: none;
`;
