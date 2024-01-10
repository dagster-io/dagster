import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  DialogFooter,
  Dialog,
  DialogBody,
  colorTextLight,
  NonIdealState,
  ExternalAnchorButton,
  Icon,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {InstigationSelector} from '../graphql/types';
import {HistoryTickFragment} from '../instigation/types/InstigationUtils.types';
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

export const TickLogDialog = ({
  tick,
  instigationSelector,
  onClose,
}: {
  tick: HistoryTickFragment;
  instigationSelector: InstigationSelector;
  onClose: () => void;
}) => {
  const {data} = useQuery<TickLogEventsQuery, TickLogEventsQueryVariables>(TICK_LOG_EVENTS_QUERY, {
    variables: {instigationSelector, tickId: Number(tick.tickId)},
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
            style={{flex: 1, color: colorTextLight()}}
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

interface TickLogTableProps {
  tick: HistoryTickFragment;
  instigationSelector: InstigationSelector;
}

export const QueryfulTickLogsTable = ({instigationSelector, tick}: TickLogTableProps) => {
  const {data, loading} = useQuery<TickLogEventsQuery, TickLogEventsQueryVariables>(
    TICK_LOG_EVENTS_QUERY,
    {
      variables: {instigationSelector, tickId: Number(tick.tickId)},
    },
  );

  const events =
    data?.instigationStateOrError.__typename === 'InstigationState' &&
    data?.instigationStateOrError.tick
      ? data?.instigationStateOrError.tick.logEvents.events
      : undefined;

  if (events && events.length) {
    return <TickLogsTable events={events} />;
  }

  const tickStatus =
    data?.instigationStateOrError.__typename === 'InstigationState'
      ? data?.instigationStateOrError.tick.status
      : undefined;
  const instigationType =
    data?.instigationStateOrError.__typename === 'InstigationState'
      ? data?.instigationStateOrError.instigationType
      : undefined;
  const instigationLoggingDocsUrl =
    instigationType === 'SENSOR'
      ? 'https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#logging-in-sensors'
      : instigationType === 'SCHEDULE'
      ? 'https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#logging-in-schedules'
      : undefined;

  return (
    <Box
      style={{height: 500}}
      flex={{justifyContent: 'center', alignItems: 'center'}}
      padding={{vertical: 48}}
    >
      {loading ? (
        'Loading logs…'
      ) : (
        <NonIdealState
          icon="no-results"
          title="No logs to display"
          description={
            <Box flex={{direction: 'column', gap: 12}}>
              <div>
                Your evaluation did not emit any logs. To learn how to emit logs in your evaluation,
                visit the documentation for more information.
              </div>
              {tickStatus === 'FAILURE' && (
                <>
                  <div>
                    For failed evaluations, logs will only be displayed if your Dagster and Dagster
                    Cloud agent versions 1.5.14 or higher.
                  </div>
                  <div>Upgrade your Dagster versions to view logs for failed evaluations.</div>
                </>
              )}
            </Box>
          }
          action={
            instigationLoggingDocsUrl && (
              <ExternalAnchorButton
                href={instigationLoggingDocsUrl}
                rightIcon={<Icon name="open_in_new" />}
              >
                View documentation
              </ExternalAnchorButton>
            )
          }
        />
      )}
    </Box>
  );
};

const TickLogsTable = ({events}: {events: TickLogEventFragment[]}) => {
  return (
    <ColumnWidthsProvider onWidthsChanged={() => {}}>
      <div style={{height: 500, position: 'relative', zIndex: 0}}>
        <Headers />
        <div style={{height: 468, overflowY: 'auto'}}>
          {events.map((event, idx) => (
            <TickLogRow event={event} key={idx} />
          ))}
        </div>
      </div>
    </ColumnWidthsProvider>
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

const TickLogRow = ({event}: {event: TickLogEventFragment}) => {
  return (
    <Row level={event.level} highlighted={false} style={{height: 'auto'}}>
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
  query TickLogEventsQuery($instigationSelector: InstigationSelector!, $tickId: Int!) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        instigationType
        tick(tickId: $tickId) {
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
