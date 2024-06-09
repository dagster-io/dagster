import {gql} from '@apollo/client';
import {Box} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {InstigationEventLogFragment} from './types/InstigationEventLogTable.types';
import {EventTypeColumn, Row, TimestampColumn} from '../runs/LogsRowComponents';
import {
  ColumnWidthsContext,
  ColumnWidthsProvider,
  Header,
  HeaderContainer,
  HeadersContainer,
} from '../runs/LogsScrollingTableHeader';

const Headers = () => {
  const widths = useContext(ColumnWidthsContext);
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

const InstigationEventLogRow = ({event}: {event: InstigationEventLogFragment}) => {
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

export const InstigationEventLogTable = ({events}: {events: InstigationEventLogFragment[]}) => {
  return (
    <ColumnWidthsProvider onWidthsChanged={() => {}}>
      <div style={{height: 500, position: 'relative', zIndex: 0}}>
        <Headers />
        <div style={{height: 468, overflowY: 'auto'}}>
          {events.map((event, idx) => (
            <InstigationEventLogRow event={event} key={idx} />
          ))}
        </div>
      </div>
    </ColumnWidthsProvider>
  );
};

export const INSTIGATION_EVENT_LOG_FRAGMENT = gql`
  fragment InstigationEventLog on InstigationEvent {
    message
    timestamp
    level
  }
`;
