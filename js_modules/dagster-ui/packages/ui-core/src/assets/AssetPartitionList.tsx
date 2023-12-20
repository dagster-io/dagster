import {
  Box,
  MiddleTruncate,
  colorBackgroundLight,
  colorBorderDefault,
  colorTextDefault,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Inner} from '../ui/VirtualizedTable';

import {AssetListRow, AssetListContainer} from './AssetEventList';
import {AssetPartitionStatus, assetPartitionStatusesToStyle} from './AssetPartitionStatus';

export interface AssetPartitionListProps {
  partitions: string[];
  statusForPartition: (dimensionKey: string) => AssetPartitionStatus[];
  focusedDimensionKey?: string;
  setFocusedDimensionKey?: (dimensionKey: string | undefined) => void;
}
export const AssetPartitionList = ({
  focusedDimensionKey,
  setFocusedDimensionKey,
  statusForPartition,
  partitions,
}: AssetPartitionListProps) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: partitions.length,
    getItemKey: (idx) => partitions[idx]!,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 36,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  React.useEffect(() => {
    if (focusedDimensionKey) {
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
                <div
                  style={{
                    gap: 4,
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr) auto',
                    alignItems: 'center',
                  }}
                  data-tooltip={dimensionKey}
                  data-tooltip-style={PartitionTooltipStyle}
                >
                  <MiddleTruncate text={dimensionKey} />
                  {/* Note: we could just state.map, but we want these in a particular order*/}
                  {state.includes(AssetPartitionStatus.MISSING) && (
                    <AssetPartitionStatusDot status={[AssetPartitionStatus.MISSING]} />
                  )}
                  {state.includes(AssetPartitionStatus.FAILED) && (
                    <AssetPartitionStatusDot status={[AssetPartitionStatus.FAILED]} />
                  )}
                  {state.includes(AssetPartitionStatus.MATERIALIZING) && (
                    <AssetPartitionStatusDot status={[AssetPartitionStatus.MATERIALIZING]} />
                  )}
                  {state.includes(AssetPartitionStatus.MATERIALIZED) && (
                    <AssetPartitionStatusDot status={[AssetPartitionStatus.MATERIALIZED]} />
                  )}
                </div>
              </Box>
            </AssetListRow>
          );
        })}
      </Inner>
    </AssetListContainer>
  );
};

export const AssetPartitionStatusDot = ({status}: {status: AssetPartitionStatus[]}) => (
  <div
    style={{
      width: 10,
      height: 10,
      borderRadius: '100%',
      flexShrink: 0,
      ...assetPartitionStatusesToStyle(status),
    }}
  />
);

const PartitionTooltipStyle = JSON.stringify({
  background: colorBackgroundLight(),
  border: `1px solid ${colorBorderDefault()}`,
  color: colorTextDefault(),
  fontSize: '14px',
  top: 0,
  left: 0,
});
