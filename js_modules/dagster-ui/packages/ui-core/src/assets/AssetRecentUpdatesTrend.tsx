import {
  Body,
  Box,
  Colors,
  Icon,
  Popover,
  Skeleton,
  useDelayedState,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AssetHealthSummary} from './AssetHealthSummary';
import styles from './css/AssetRecentUpdatesTrend.module.css';
import {
  AssetFailedToMaterializeFragment,
  AssetObservationFragment,
  AssetSuccessfulMaterializationFragment,
} from './types/useRecentAssetEvents.types';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {useRefreshAtInterval} from '../app/QueryRefresh';
import {Timestamp} from '../app/time/Timestamp';
import {AssetLatestInfoFragment} from '../asset-data/types/AssetBaseDataProvider.types';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
import {TimeFromNow} from '../ui/TimeFromNow';

const INTERVAL_MSEC = 30 * 1000;

export const AssetRecentUpdatesTrend = React.memo(({asset}: {asset: AssetHealthFragment}) => {
  // Wait 100ms to avoid querying during fast scrolling of the table
  const shouldQuery = useDelayedState(500);
  const {
    events: _events,
    latestInfo,
    loading,
    refetch,
  } = useRecentAssetEvents(shouldQuery ? asset.key : undefined, 5, [
    AssetEventHistoryEventTypeSelector.MATERIALIZATION,
    AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
    AssetEventHistoryEventTypeSelector.OBSERVATION,
  ]);

  const {events} = useMemo(() => {
    if (!latestInfo?.inProgressRunIds.length && !latestInfo?.unstartedRunIds.length) {
      return {events: _events};
    }
    return {events: [latestInfo, ..._events]};
  }, [latestInfo, _events]);

  useRefreshAtInterval({
    refresh: refetch,
    intervalMs: INTERVAL_MSEC,
    enabled: shouldQuery,
  });

  const states = useMemo(() => {
    return new Array(5).fill(null).map((_, _index) => {
      const index = 4 - _index;
      const event = events[index];
      if (!event) {
        return (
          <div
            key={index}
            className={styles.pill}
            style={{
              background: Colors.backgroundDisabled(),
              opacity: OPACITIES[index] ?? 1,
            }}
          />
        );
      }
      if (event.__typename === 'AssetLatestInfo') {
        return (
          <EventPopover key={index} event={event}>
            <div
              className={styles.pill}
              style={{
                background: Colors.accentBlue(),
                opacity: OPACITIES[index] ?? 1,
              }}
            />
          </EventPopover>
        );
      }
      if (event.__typename === 'FailedToMaterializeEvent') {
        return (
          <EventPopover key={index} event={event}>
            <div
              className={styles.pill}
              style={{
                background: Colors.accentRed(),
                opacity: OPACITIES[index] ?? 1,
              }}
            />
          </EventPopover>
        );
      }
      return (
        <EventPopover key={index} event={event}>
          <div
            className={styles.pill}
            style={{
              background: Colors.accentGreen(),
              opacity: OPACITIES[index] ?? 1,
            }}
          />
        </EventPopover>
      );
    });
  }, [events]);

  const lastEvent = _events[0];

  return (
    <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
      {(loading || !shouldQuery) && !lastEvent ? (
        <Skeleton $width={100} $height={21} />
      ) : (
        <>
          <EventPopover event={lastEvent}>
            {lastEvent ? (
              <Body color={Colors.textLight()}>
                <TimeFromNow
                  unixTimestamp={Number(lastEvent.timestamp) / 1000}
                  showTooltip={false}
                />
              </Body>
            ) : (
              ' - '
            )}
          </EventPopover>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>{states}</Box>
          <div style={{height: 13, width: 1, background: Colors.keylineDefault()}} />
        </>
      )}
      <AssetHealthSummary assetKey={asset.key} iconOnly />
    </Box>
  );
});

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
      | AssetLatestInfoFragment
      | undefined;
    children: React.ReactNode;
  }) => {
    const {content, icon, runId, timestamp} = useMemo(() => {
      switch (event?.__typename) {
        case 'AssetLatestInfo':
          if (event.latestRun?.status === 'STARTED') {
            return {
              content: <Body>In progress</Body>,
              icon: <Icon name="run_started" color={Colors.accentBlue()} />,
              runId: event.latestRun!.id,
              timestamp: Number(event.latestRun!.startTime) * 1000,
            };
          }
          return {
            content: <Body>Queued</Body>,
            icon: <Icon name="run_queued" color={Colors.accentBlue()} />,
            runId: event.latestRun!.id,
            timestamp: null,
          };
        case 'FailedToMaterializeEvent':
          return {
            content: <Body>Failed</Body>,
            icon: <Icon name="run_failed" color={Colors.accentRed()} />,
            runId: event.runId,
            timestamp: event.timestamp,
          };
        case 'ObservationEvent':
          return {
            content: <Body>Observed</Body>,
            icon: <Icon name="run_success" color={Colors.accentGreen()} />,
            runId: event.runId,
            timestamp: event.timestamp,
          };
        case 'MaterializationEvent':
          return {
            content: <Body>Materialized</Body>,
            icon: <Icon name="run_success" color={Colors.accentGreen()} />,
            runId: event.runId,
            timestamp: event.timestamp,
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
            {timestamp ? (
              <Box padding={{vertical: 8, horizontal: 12}} border="bottom">
                <Timestamp timestamp={{ms: Number(timestamp)}} />
              </Box>
            ) : null}
            <Box padding={{vertical: 8, horizontal: 12}}>
              <Link to={`/runs/${runId}`}>
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
