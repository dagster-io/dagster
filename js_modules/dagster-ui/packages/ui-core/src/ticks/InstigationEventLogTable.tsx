import {Box} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useContext, useEffect, useRef} from 'react';

import {InstigationEventLogFragment} from './types/InstigationEventLogTable.types';
import {gql} from '../apollo-client';
import {EventTypeColumn, Row as LogsRow, TimestampColumn} from '../runs/LogsRowComponents';
import {
  ColumnWidthsContext,
  ColumnWidthsProvider,
  Header,
  HeaderContainer,
  HeadersContainer,
} from '../runs/LogsScrollingTableHeader';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

const Headers = () => {
  const widths = useContext(ColumnWidthsContext);
  return (
    <HeadersContainer>
      <Header
        width={widths.eventType}
        onResize={(width) => widths.onChange({...widths, eventType: width})}
      >
        Type
      </Header>
      <Header
        width={widths.timestamp}
        onResize={(width) => widths.onChange({...widths, timestamp: width})}
      >
        Timestamp
      </Header>
      <HeaderContainer style={{flex: 1}}>Event</HeaderContainer>
    </HeadersContainer>
  );
};

export const InstigationEventLogTable = ({events}: {events: InstigationEventLogFragment[]}) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 28,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();
  const isAtBottom = useRef(true);

  useEffect(() => {
    const el = parentRef.current;
    if (!el || !('scrollTo' in el)) {
      return; // scrollTo is not present in jest test
    }
    if (isAtBottom.current && events.length) {
      el.scrollTo(0, el.scrollHeight);
    }
    const onScroll = () => {
      isAtBottom.current = el.scrollTop >= el.scrollHeight - el.clientHeight;
    };
    el.addEventListener('scroll', onScroll);
    return () => el.removeEventListener('scroll', onScroll);
  });

  return (
    <ColumnWidthsProvider onWidthsChanged={() => {}}>
      <Headers />
      <Container ref={parentRef} style={{position: 'relative'}}>
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const event = events[index]!;
            return (
              <Row key={key} $start={start} $height={size}>
                <LogsRow
                  level={event.level}
                  highlighted={false}
                  data-index={index}
                  ref={rowVirtualizer.measureElement}
                  style={{height: 'auto', maxHeight: 'unset'}}
                >
                  <EventTypeColumn>
                    <span style={{marginLeft: 8}}>{event.level}</span>
                  </EventTypeColumn>
                  <TimestampColumn time={event.timestamp} />
                  <Box padding={{horizontal: 12, vertical: 4}} style={{flex: 1}}>
                    {event.message}
                  </Box>
                </LogsRow>
              </Row>
            );
          })}
        </Inner>
      </Container>
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
