import {
  Body,
  Box,
  Colors,
  Icon,
  Popover,
  Skeleton,
  useDelayedState,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AssetHealthSummary} from './AssetHealthSummary';
import {useAllAssets} from './AssetsCatalogTable';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {Timestamp} from '../app/time/Timestamp';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {
  AssetFailedToMaterializeFragment,
  AssetObservationFragment,
  AssetSuccessfulMaterializationFragment,
} from './types/useRecentAssetEvents.types';

export const AssetRecentUpdatesTrend = React.memo(({asset}: {asset: AssetHealthFragment}) => {
  const {assetsByAssetKey} = useAllAssets();
  const assetDefinition = assetsByAssetKey.get(tokenForAssetKey(asset.assetKey))?.definition;
  // Wait 100ms to avoid querying during fast scrolling of the table
  const shouldQuery = useDelayedState(100);
  const {materializations, observations, loading} = useRecentAssetEvents(
    shouldQuery ? asset.assetKey : undefined,
    {limit: 5},
    {assetHasDefinedPartitions: !!assetDefinition?.partitionDefinition},
  );

  const states = useMemo(() => {
    return new Array(5).fill(null).map((_, _index) => {
      const index = 4 - _index;
      const materialization = materializations[index] ?? observations[index];
      if (!materialization) {
        return <Pill key={index} $index={index} $color={Colors.backgroundDisabled()} />;
      }
      if (materialization.__typename === 'FailedToMaterializeEvent') {
        return (
          <EventPopover key={index} event={materialization}>
            <Pill $index={index} $color={Colors.accentRed()} />
          </EventPopover>
        );
      }
      return (
        <EventPopover key={index} event={materialization}>
          <Pill $index={index} $color={Colors.accentGreen()} />
        </EventPopover>
      );
    });
  }, [materializations, observations]);

  const lastEvent = materializations[0] ?? observations[0];

  const timeAgo = useMemo(() => {
    if (!lastEvent) {
      return ' - ';
    }
    return dayjs(Number(lastEvent.timestamp)).fromNow();
  }, [lastEvent]);

  return (
    <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
      {loading && !lastEvent ? (
        <Skeleton $width={100} $height={21} />
      ) : (
        <>
          <EventPopover event={lastEvent}>
            <Body color={Colors.textLight()}>{timeAgo}</Body>
          </EventPopover>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>{states}</Box>
          <div style={{height: 13, width: 1, background: Colors.keylineDefault()}} />
        </>
      )}
      <AssetHealthSummary assetKey={asset.assetKey} iconOnly />
    </Box>
  );
});

const Pill = styled.div<{$index: number; $color: string}>`
  border-radius: 2px;
  height: 16px;
  width: 6px;
  background: ${({$color}) => $color};
  opacity: ${({$index}) => OPACITIES[$index] ?? 1};
  &:hover {
    box-shadow: 0 0 0 1px ${Colors.accentGrayHover()};
  }
`;

const OPACITIES: Record<number, number> = {
  0: 1,
  1: 0.8,
  2: 0.66,
  3: 0.4,
  4: 0.2,
};

const EventPopover = React.memo(
  ({
    event,
    children,
  }: {
    event:
      | AssetFailedToMaterializeFragment
      | AssetObservationFragment
      | AssetSuccessfulMaterializationFragment
      | undefined;
    children: React.ReactNode;
  }) => {
    const {content, icon} = useMemo(() => {
      switch (event?.__typename) {
        case 'FailedToMaterializeEvent':
          return {
            content: <Body>Failed</Body>,
            icon: <Icon name="run_failed" color={Colors.accentRed()} />,
          };
        case 'ObservationEvent':
          return {
            content: <Body>Observed</Body>,
            icon: <Icon name="run_success" color={Colors.accentGreen()} />,
          };
        case 'MaterializationEvent':
          return {
            content: <Body>Materialized</Body>,
            icon: <Icon name="run_success" color={Colors.accentGreen()} />,
          };
        default:
          return {content: null, icon: null};
      }
    }, [event]);
    if (!event) {
      return children;
    }
    return (
      <Popover
        interactionKind="hover"
        content={
          <Box border="all">
            <Box padding={{vertical: 8, horizontal: 12}} border="bottom">
              <Timestamp timestamp={{ms: Number(event.timestamp)}} />
            </Box>
            <Box padding={{vertical: 8, horizontal: 12}}>
              <Link to={`/runs/${event.runId}`}>
                <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                  {icon}
                  {content}
                </Box>
              </Link>
            </Box>
          </Box>
        }
      >
        {children}
      </Popover>
    );
  },
);
