import {Box, Colors, NonIdealState, Row} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useEffect, useRef} from 'react';
import styled from 'styled-components';

import {LogFilter, LogsProviderLogs} from './LogsProvider';
import {Structured, Unstructured} from './LogsRow';
import {ColumnWidthsProvider, Headers} from './LogsScrollingTableHeader';
import {IRunMetadataDict} from './RunMetadataProvider';
import {filterLogs} from './filterLogs';
import {Container, Inner} from '../ui/VirtualizedTable';

const BOTTOM_SCROLL_THRESHOLD_PX = 60;

interface Props {
  logs: LogsProviderLogs;
  filter: LogFilter;
  filterStepKeys: string[];

  // We use this string to know whether the changes to `nodes` require us to
  // re-layout the entire table. Appending new rows can be done very fast, but
  // removing some rows requires the whole list be "reflowed" again. Checking
  // `nodes` for equality doesn't let us optimize for the append- case.
  filterKey: string;
  metadata: IRunMetadataDict;
}

export const LogsScrollingTable = (props: Props) => {
  const {filterStepKeys, metadata, filter, logs} = props;

  const parentRef = useRef<HTMLDivElement>(null);
  const pinToBottom = useRef(true);

  const {filteredNodes, textMatchNodes} = filterLogs(logs, filter, filterStepKeys);

  const virtualizer = useVirtualizer({
    count: filteredNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 20,
    paddingEnd: 40,
  });

  const totalHeight = virtualizer.getTotalSize();
  const items = virtualizer.getVirtualItems();

  // Determine whether the user has scrolled away from the bottom of the log list.
  // If so, we no longer pin to the bottom of the list as new logs arrive. If they
  // scroll back to the bottom, we go back to pinning.
  useEffect(() => {
    const parent = parentRef.current;

    const onScroll = () => {
      const totalHeight = virtualizer.getTotalSize();
      const rectHeight = virtualizer.scrollRect.height;
      const scrollOffset = virtualizer.scrollOffset;

      // If we're within a certain threshold of the maximum scroll depth, consider this
      // to mean that the user wants to pin scrolling to the bottom.
      const maxScrollOffset = totalHeight - rectHeight;
      const shouldPin = scrollOffset > maxScrollOffset - BOTTOM_SCROLL_THRESHOLD_PX;

      pinToBottom.current = shouldPin;
    };

    parent && parent.addEventListener('scroll', onScroll);
    return () => {
      parent && parent.removeEventListener('scroll', onScroll);
    };
  }, [virtualizer]);

  // If we should pin to the bottom, do so when the height of the virtualized table changes.
  useEffect(() => {
    if (pinToBottom.current) {
      virtualizer.scrollToOffset(totalHeight, {align: 'end'});
    }
  }, [totalHeight, virtualizer]);

  const content = () => {
    if (logs.loading) {
      return (
        <Box margin={{top: 32}}>
          <ListEmptyState>
            <NonIdealState icon="spinner" title="Fetching logs..." />
          </ListEmptyState>
        </Box>
      );
    }

    if (Object.keys(filter.levels).length === 0) {
      return (
        <Box margin={{top: 32}}>
          <NonIdealState
            icon="search"
            title="No levels selected"
            description="You have not selected any log levels. Choose at least one level to view logs."
          />
        </Box>
      );
    }

    return (
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const node = filteredNodes[index]!;
          const textMatch = textMatchNodes.includes(node);
          const focusedTimeMatch = Number(node.timestamp) === filter.focusedTime;
          const highlighted = textMatch || focusedTimeMatch;

          const row =
            node.__typename === 'LogMessageEvent' ? (
              <Unstructured node={node} metadata={metadata} highlighted={highlighted} />
            ) : (
              <Structured node={node} metadata={metadata} highlighted={highlighted} />
            );

          return (
            <Row $height={size} $start={start} key={key}>
              <div
                ref={virtualizer.measureElement}
                data-index={index}
                style={{position: 'relative'}}
              >
                {row}
              </div>
            </Row>
          );
        })}
      </Inner>
    );
  };

  return (
    <ColumnWidthsProvider>
      <Headers />
      <Container ref={parentRef}>{content()}</Container>
    </ColumnWidthsProvider>
  );
};

export const ListEmptyState = styled.div`
  background-color: ${Colors.backgroundDefault()};
  z-index: 100;
  position: absolute;
  width: 100%;
  height: calc(100% - 50px);
`;
