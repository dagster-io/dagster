import {Box, Caption, Colors, Subtitle2, useViewport} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import styled from 'styled-components';

import {useRecentAssetEvents} from './useRecentAssetEvents';
import {AssetKeyInput} from '../graphql/types';
import {useFormatDateTime} from '../ui/useFormatDateTime';

const MIN_TICK_WIDTH = 20;

export const RecentUpdatesTimeline = ({assetKey}: {assetKey: AssetKeyInput}) => {
  const {materializations} = useRecentAssetEvents(assetKey, {}, {assetHasDefinedPartitions: false});

  if (!materializations.length) {
    return null;
  }
  return <RecentUpdatesTimelineImpl materializations={materializations} />;
};

const RecentUpdatesTimelineImpl = ({
  materializations,
}: {
  materializations: ReturnType<typeof useRecentAssetEvents>['materializations'];
}) => {
  const {containerProps, viewport} = useViewport();
  const widthAvailablePerTick = viewport.width / materializations.length;

  const tickWidth = Math.min(widthAvailablePerTick, MIN_TICK_WIDTH);

  const buckets = Math.ceil(viewport.width / tickWidth);

  const endTimestamp = parseInt(materializations[0]!.timestamp);
  const startTimestamp = parseInt(materializations[materializations.length - 1]!.timestamp);
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
          {bucketedMaterializations.map((bucket) => (
            <Tick
              key={bucket.start}
              style={{
                left: tickWidth * bucket.start,
                width: tickWidth * (bucket.end - bucket.start) - 1,
              }}
            >
              {bucket.materializations.length}
            </Tick>
          ))}
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

const Tick = styled.div`
  position: absolute;
  top: 0;
  bottom: 0;
  background-color: ${Colors.accentGreen()};
  color: ${Colors.backgroundDefault()};
  cursor: pointer;
  border-radius: 200px;
  display: grid;
  place-content: center;
  &:hover {
    background-color: ${Colors.accentGreenHover()};
  }
`;
