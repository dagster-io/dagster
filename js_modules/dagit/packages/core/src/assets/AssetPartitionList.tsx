import {Box, Colors, Icon} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PartitionState, partitionStateToColor} from '../partitions/PartitionStatus';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

export const AssetPartitionList: React.FC<{
  partitions: {dimensionKey: string; state: PartitionState}[];
  focusedDimensionKey?: string;
  setFocusedDimensionKey?: (dimensionKey: string | undefined) => void;
}> = ({focusedDimensionKey, setFocusedDimensionKey, partitions}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: partitions.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 36,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  React.useEffect(() => {
    if (focusedDimensionKey) {
      rowVirtualizer.scrollToIndex(
        partitions.findIndex((p) => p.dimensionKey === focusedDimensionKey),
        {smoothScroll: false, align: 'auto'},
      );
    }
  }, [focusedDimensionKey, rowVirtualizer, partitions]);

  return (
    <Container
      ref={parentRef}
      tabIndex={-1}
      onKeyDown={(e) => {
        const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
        if (!setFocusedDimensionKey || !shift || !focusedDimensionKey || e.isDefaultPrevented()) {
          return;
        }
        const nextIdx = partitions.findIndex((p) => p.dimensionKey === focusedDimensionKey) + shift;
        const next = partitions[nextIdx];
        if (next) {
          e.preventDefault();
          setFocusedDimensionKey(next.dimensionKey);
        }
      }}
    >
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const {dimensionKey, state} = partitions[index];

          return (
            <ClickableRow
              key={key}
              $height={size}
              $start={start}
              $focused={dimensionKey === focusedDimensionKey}
              onClick={(e) => {
                // If you're interacting with something in the row, don't trigger a focus change.
                // Since focus is stored in the URL bar this overwrites any link click navigation.
                // We could alternatively e.preventDefault() on every link but it's easy to forget.
                if (e.target instanceof HTMLElement && e.target.closest('a')) {
                  return;
                }
                setFocusedDimensionKey?.(
                  focusedDimensionKey !== dimensionKey ? dimensionKey : undefined,
                );
              }}
            >
              <Box
                style={{height: size}}
                padding={{left: 24, right: 12}}
                flex={{direction: 'column', justifyContent: 'center', gap: 8}}
                border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              >
                <AssetPartitionListRow dimensionKey={dimensionKey} state={state} />
              </Box>
            </ClickableRow>
          );
        })}
      </Inner>
    </Container>
  );
};

const ClickableRow = styled(Row)<{$focused: boolean}>`
  cursor: pointer;

  :focus,
  :active,
  :hover {
    outline: none;
    background: ${Colors.White};
  }
  ${(p) =>
    p.$focused &&
    `background: ${Colors.White};
    `}
`;

const AssetPartitionListRow: React.FC<{dimensionKey: string; state: PartitionState}> = ({
  dimensionKey,
  state,
}) => {
  return (
    <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
      <Icon name="partition" />
      {dimensionKey}
      <div style={{flex: 1}} />
      {(state === PartitionState.SUCCESS_MISSING || state === PartitionState.SUCCESS) && (
        <StateDot state={PartitionState.SUCCESS} />
      )}
      {(state === PartitionState.SUCCESS_MISSING || state === PartitionState.MISSING) && (
        <StateDot state={PartitionState.MISSING} />
      )}
    </Box>
  );
};

const StateDot = ({state}: {state: PartitionState}) => (
  <div
    key={state}
    style={{
      width: 10,
      height: 10,
      borderRadius: '100%',
      marginLeft: -5,
      background: partitionStateToColor(state),
    }}
  />
);
