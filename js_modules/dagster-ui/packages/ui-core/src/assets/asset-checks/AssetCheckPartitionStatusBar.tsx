import {Tooltip, useViewport} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';

import {
  AssetCheckPartitionStatus,
  assetCheckPartitionStatusToText,
  assetCheckPartitionStatusesToStyle,
} from './AssetCheckPartitionStatus';
import styles from '../../partitions/PartitionStatusBar.module.css';
import {assembleIntoSpans} from '../../partitions/SpanRepresentation';
import {
  MIN_PARTITION_SPAN_WIDTH,
  PARTITION_STATUS_BAR_HEIGHT,
} from '../../partitions/partitionConstants';
import {usePartitionDragSelection} from '../../partitions/usePartitionDragSelection';

interface AssetCheckPartitionStatusBarProps {
  partitionKeys: string[];
  statusForPartition: (key: string) => AssetCheckPartitionStatus;
  selected?: string[];
  onSelect?: (selected: string[]) => void;
  splitPartitions?: boolean;
}

type ColorSegment = {
  start: {idx: number; key: string};
  end: {idx: number; key: string};
  status: AssetCheckPartitionStatus;
  style: React.CSSProperties;
  label: string;
};

export const AssetCheckPartitionStatusBar = React.memo(
  ({
    partitionKeys,
    statusForPartition,
    selected,
    onSelect,
    splitPartitions = false,
  }: AssetCheckPartitionStatusBarProps) => {
    const ref = React.useRef<HTMLDivElement>(null);
    const {viewport, containerProps} = useViewport();

    // Use shared drag selection logic
    const {currentSelectionRange, selectedSpans, handleMouseDown} = usePartitionDragSelection({
      partitionKeys,
      selected,
      onSelect,
      containerRef: ref,
    });

    // Build segments from partition data
    const segments: ColorSegment[] = useMemo(() => {
      const spans = assembleIntoSpans(partitionKeys, (key) => statusForPartition(key));
      return spans
        .map((span) => {
          const startKey = partitionKeys[span.startIdx];
          const endKey = partitionKeys[span.endIdx];
          if (!startKey || !endKey) {
            return null;
          }
          return {
            start: {idx: span.startIdx, key: startKey},
            end: {idx: span.endIdx, key: endKey},
            status: span.status,
            style: assetCheckPartitionStatusesToStyle([span.status]),
            label: assetCheckPartitionStatusToText(span.status),
          };
        })
        .filter((s): s is ColorSegment => s !== null);
    }, [partitionKeys, statusForPartition]);

    const highestIndex = segments
      .map((s) => s.end.idx)
      .reduce((prev, cur) => Math.max(prev, cur), 0);
    const indexToPct = (idx: number) => `${((idx * 100) / partitionKeys.length).toFixed(3)}%`;
    const showSeparators =
      splitPartitions && viewport.width > MIN_PARTITION_SPAN_WIDTH * (partitionKeys.length + 1);

    return (
      <div
        {...containerProps}
        onMouseDown={(e) => e.preventDefault()}
        onDragStart={(e) => e.preventDefault()}
      >
        {selected && selected.length > 0 ? (
          <div className={styles.selectionSpansContainer}>
            {selectedSpans.map((s) => (
              <div
                className={styles.selectionSpan}
                key={s.startIdx}
                style={{
                  left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
                  width: indexToPct(s.endIdx - s.startIdx + 1),
                }}
              />
            ))}
          </div>
        ) : null}
        <div
          className={styles.partitionSpansContainer}
          style={{'--height': `${PARTITION_STATUS_BAR_HEIGHT}px`} as React.CSSProperties}
          ref={ref}
          onMouseDown={handleMouseDown}
        >
          {segments.map((s) => (
            <div
              key={s.start.idx}
              style={{
                left: `min(calc(100% - 2px), ${indexToPct(s.start.idx)})`,
                width: indexToPct(s.end.idx - s.start.idx + 1),
                minWidth: 1,
                position: 'absolute',
                zIndex: s.start.idx === 0 || s.end.idx === highestIndex ? 3 : 2,
                top: 0,
              }}
            >
              <Tooltip
                display="block"
                position="top"
                content={
                  s.start.idx === s.end.idx
                    ? `Partition ${partitionKeys[s.start.idx]} is ${s.label.toLowerCase()}`
                    : `Partitions ${partitionKeys[s.start.idx]} through ${
                        partitionKeys[s.end.idx]
                      } are ${s.label.toLowerCase()}`
                }
              >
                <div className={styles.colorSpan} style={s.style} />
              </Tooltip>
            </div>
          ))}
          {showSeparators
            ? segments.slice(1).map((s) => (
                <div
                  className={styles.separator}
                  key={`separator_${s.start.idx}`}
                  style={{
                    left: `min(calc(100% - 2px), ${indexToPct(s.start.idx)})`,
                    height: PARTITION_STATUS_BAR_HEIGHT,
                  }}
                />
              ))
            : null}
          {currentSelectionRange ? (
            <div
              className={styles.selectionHoverHighlight}
              style={{
                left: `min(calc(100% - 2px), ${indexToPct(
                  Math.min(
                    partitionKeys.indexOf(currentSelectionRange.start),
                    partitionKeys.indexOf(currentSelectionRange.end),
                  ),
                )})`,
                width: indexToPct(
                  Math.abs(
                    partitionKeys.indexOf(currentSelectionRange.end) -
                      partitionKeys.indexOf(currentSelectionRange.start),
                  ) + 1,
                ),
                height: PARTITION_STATUS_BAR_HEIGHT,
              }}
            />
          ) : null}
        </div>
      </div>
    );
  },
);
