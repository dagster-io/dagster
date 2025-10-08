import {Body, Box, Colors, Icon, Popover} from '@dagster-io/ui-components';
import React, {ReactNode, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from '../app/time/Timestamp';
import {RunStatus} from '../graphql/types';
import {PezItem, calculatePezOpacity} from '../ui/PezItem';

interface Props {
  latestInfo?: EventForPopover;
  events: EventForPopover[];
}

export const AssetRecentUpdatesTrend = React.memo(({latestInfo, events}: Props) => {
  const items = latestInfo ? [latestInfo, ...events.slice(0, 4)] : events.slice(0, 5);
  const emptyItems = new Array(Math.max(5 - items.length, 0)).fill(null);
  const allItems = [...items, ...emptyItems].reverse();

  const states = allItems.map((event, index) => {
    const opacity = calculatePezOpacity(index, 5);

    const key = () => {
      switch (event?.__typename) {
        case 'AssetLatestInfo':
          return event.latestRun?.id ?? index;
        case 'FailedToMaterializeEvent':
        case 'ObservationEvent':
        case 'MaterializationEvent':
          return event.runId;
        default:
          return index;
      }
    };

    if (!event) {
      return <PezItem key={key()} opacity={opacity} color={Colors.backgroundDisabled()} />;
    }

    const color = () => {
      switch (event.__typename) {
        case 'AssetLatestInfo':
          return Colors.accentBlue();
        case 'FailedToMaterializeEvent':
          return Colors.accentRed();
        default:
          return Colors.accentGreen();
      }
    };

    return (
      <EventPopover key={key()} event={event}>
        <PezItem opacity={opacity} color={color()} />
      </EventPopover>
    );
  });

  return <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>{states}</Box>;
});

type EventForPopover =
  | {
      __typename: 'AssetLatestInfo';
      latestRun: null | {
        id: string;
        status: RunStatus;
        startTime: number | null;
      };
    }
  | {__typename: 'FailedToMaterializeEvent'; runId: string; timestamp: string}
  | {__typename: 'ObservationEvent'; runId: string; timestamp: string}
  | {__typename: 'MaterializationEvent'; runId: string; timestamp: string};

export const EventPopover = React.memo(
  ({event, children}: {event?: EventForPopover; children: ReactNode}) => {
    const {content, icon, runId, timestamp} = useMemo(() => {
      switch (event?.__typename) {
        case 'AssetLatestInfo': {
          const {latestRun} = event;
          if (!latestRun) {
            return {content: null, icon: null};
          }
          if (latestRun.status === 'STARTED') {
            return {
              content: <Body>In progress</Body>,
              icon: <Icon name="run_started" color={Colors.accentBlue()} />,
              runId: latestRun.id,
              timestamp: Number(latestRun.startTime) * 1000,
            };
          }
          return {
            content: <Body>Queued</Body>,
            icon: <Icon name="run_queued" color={Colors.accentBlue()} />,
            runId: latestRun.id,
            timestamp: null,
          };
        }
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
        placement="top"
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
