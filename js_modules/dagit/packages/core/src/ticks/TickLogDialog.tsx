import {gql, useQuery} from '@apollo/client';
import {Box, Button, DialogFooter, Dialog, Colors, DialogBody} from '@dagster-io/ui';
import * as React from 'react';

import {InstigationSelector} from '../graphql/types';
import {HistoryTickFragment} from '../instigation/types/TickHistory.types';
import {EventTypeColumn, TimestampColumn, Row} from '../runs/LogsRowComponents';
import {
  ColumnWidthsProvider,
  ColumnWidthsContext,
  HeadersContainer,
  HeaderContainer,
  Header,
} from '../runs/LogsScrollingTableHeader';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

import {
  TickLogEventsQuery,
  TickLogEventsQueryVariables,
  TickLogEventFragment,
} from './types/TickLogDialog.types';

export const TickLogDialog: React.FC<{
  tick: HistoryTickFragment;
  instigationSelector: InstigationSelector;
  onClose: () => void;
}> = ({tick, instigationSelector, onClose}) => {
  const {data} = useQuery<TickLogEventsQuery, TickLogEventsQueryVariables>(TICK_LOG_EVENTS_QUERY, {
    variables: {instigationSelector, timestamp: tick.timestamp},
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  const events =
    data?.instigationStateOrError.__typename === 'InstigationState' &&
    data?.instigationStateOrError.tick
      ? data?.instigationStateOrError.tick.logEvents.events
      : undefined;

  return (
    <Dialog
      isOpen={!!events}
      onClose={onClose}
      style={{width: '70vw', display: 'flex'}}
      title={tick ? <TimestampDisplay timestamp={tick.timestamp} /> : null}
    >
      <DialogBody>
        {events && events.length ? (
          <TickLogsTable events={events} />
        ) : (
          <Box
            flex={{justifyContent: 'center', alignItems: 'center'}}
            style={{flex: 1, color: Colors.Gray600}}
          >
            No logs available
          </Box>
        )}
      </DialogBody>
      <DialogFooter>
        <Button intent="primary" onClick={onClose}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const TickLogsTable: React.FC<{events: TickLogEventFragment[]}> = ({events}) => {
  return (
    <div style={{overflow: 'hidden', borderBottom: '0.5px solid #ececec', flex: 1}}>
      <ColumnWidthsProvider onWidthsChanged={() => {}}>
        <Headers />
        {events.map((event, idx) => (
          <TickLogRow event={event} key={idx} />
        ))}
      </ColumnWidthsProvider>
    </div>
  );
};

const Headers = () => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <HeadersContainer>
      <Header
        width={widths.eventType}
        onResize={(width) => widths.onChange({...widths, eventType: width})}
      >
        Event Type
      </Header>
      <HeaderContainer style={{flex: 1}}>Info</HeaderContainer>
      <Header
        handleSide="left"
        width={widths.timestamp}
        onResize={(width) => widths.onChange({...widths, timestamp: width})}
      >
        Timestamp
      </Header>
    </HeadersContainer>
  );
};

const TickLogRow: React.FC<{event: TickLogEventFragment}> = ({event}) => {
  return (
    <Row level={event.level} highlighted={false}>
      <EventTypeColumn>
        <span style={{marginLeft: 8}}>{event.level}</span>
      </EventTypeColumn>
      <Box padding={{horizontal: 12}} style={{flex: 1}}>
        {event.message}
      </Box>
      <TimestampColumn time={event.timestamp} />
    </Row>
  );
};

const TICK_LOG_EVENTS_QUERY = gql`
  query TickLogEventsQuery($instigationSelector: InstigationSelector!, $timestamp: Float!) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        tick(timestamp: $timestamp) {
          id
          status
          timestamp
          logEvents {
            events {
              ...TickLogEvent
            }
          }
        }
      }
    }
  }

  fragment TickLogEvent on InstigationEvent {
    message
    timestamp
    level
  }
`;
