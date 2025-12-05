import {Box, Colors, MiddleTruncate} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {CSSProperties, useEffect, useRef} from 'react';

import {AssetListContainer, AssetListRow} from './AssetEventList';
import {Inner} from '../ui/VirtualizedTable';

export interface PartitionListSelectorProps<TStatus> {
  partitions: string[];
  statusForPartition: (dimensionKey: string) => TStatus[];
  focusedDimensionKey?: string;
  setFocusedDimensionKey?: (dimensionKey: string | undefined) => void;
  statusesToStyle: (statuses: TStatus[]) => CSSProperties;
  statusOrder: TStatus[];
}

export function PartitionListSelector<TStatus>({
  focusedDimensionKey,
  setFocusedDimensionKey,
  statusForPartition,
  partitions,
  statusesToStyle,
  statusOrder,
}: PartitionListSelectorProps<TStatus>) {
  const parentRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: partitions.length,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    getItemKey: (idx) => partitions[idx]!,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 36,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  useEffect(() => {
    if (focusedDimensionKey && partitions.indexOf(focusedDimensionKey) !== -1) {
      rowVirtualizer.scrollToIndex(partitions.indexOf(focusedDimensionKey), {
        behavior: 'auto',
        align: 'auto',
      });
    }
  }, [focusedDimensionKey, rowVirtualizer, partitions]);

  return (
    <AssetListContainer
      ref={parentRef}
      tabIndex={-1}
      onKeyDown={(e) => {
        const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
        if (!setFocusedDimensionKey || !shift || !focusedDimensionKey || e.isDefaultPrevented()) {
          return;
        }
        const nextIdx = partitions.indexOf(focusedDimensionKey) + shift;
        const next = partitions[nextIdx];
        if (next) {
          e.preventDefault();
          setFocusedDimensionKey(next);
        }
      }}
    >
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          const dimensionKey = partitions[index]!;
          const state = statusForPartition(dimensionKey);
          return (
            <AssetListRow
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
                border="bottom"
              >
                <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
                  <div
                    style={{flex: 1, minWidth: 0}}
                    data-tooltip={dimensionKey}
                    data-tooltip-style={PartitionTooltipStyle}
                  >
                    <MiddleTruncate text={dimensionKey} />
                  </div>
                  {/* Show status dots in the specified order */}
                  {statusOrder.map((status) => {
                    if (state.includes(status)) {
                      return (
                        <PartitionStatusDot
                          key={String(status)}
                          status={[status]}
                          statusesToStyle={statusesToStyle}
                        />
                      );
                    }
                    return null;
                  })}
                </Box>
              </Box>
            </AssetListRow>
          );
        })}
      </Inner>
    </AssetListContainer>
  );
}

export const PartitionStatusDot = <TStatus,>({
  status,
  statusesToStyle,
}: {
  status: TStatus[];
  statusesToStyle: (statuses: TStatus[]) => CSSProperties;
}) => (
  <div
    style={{
      width: 10,
      height: 10,
      borderRadius: '100%',
      flexShrink: 0,
      ...statusesToStyle(status),
    }}
  />
);

const PartitionTooltipStyle = JSON.stringify({
  background: Colors.backgroundLight(),
  border: `1px solid ${Colors.borderDefault()}`,
  color: Colors.textDefault(),
  fontSize: '14px',
  top: 0,
  left: 0,
});
