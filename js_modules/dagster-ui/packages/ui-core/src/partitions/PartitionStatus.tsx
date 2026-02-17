import {Box, Colors, Tooltip, useViewport} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';
import {useMemo} from 'react';

import styles from './PartitionStatusBar.module.css';
import {assembleIntoSpans} from './SpanRepresentation';
import {MIN_PARTITION_SPAN_WIDTH} from './partitionConstants';
import {usePartitionDragSelection} from './usePartitionDragSelection';
import {
  assetPartitionStatusToText,
  assetPartitionStatusesToStyle,
} from '../assets/AssetPartitionStatus';
import {Range} from '../assets/usePartitionHealthData';
import {RunStatus} from '../graphql/types';
import {RUN_STATUS_COLORS, runStatusToBackfillStateString} from '../runs/RunStatusTag';
import {assertExists} from '../util/invariant';

// This component can be wired up to assets, which provide partition status in terms
// of ranges with a given status. It can also be wired up to backfills, which provide
// status per-partition.
//
// In the latter case, this component will call the getter function you provide
// and assemble ranges by itself for display.
//
type PartitionStatusHealthSourceAssets = {
  ranges: Range[];
};
export type PartitionStatusHealthSourceOps = {
  runStatusForPartitionKey: (partitionKey: string, partitionIdx: number) => RunStatus | undefined;
};

export type PartitionStatusHealthSource =
  | PartitionStatusHealthSourceOps
  | PartitionStatusHealthSourceAssets;

interface PartitionStatusProps {
  partitionNames: string[];
  health: PartitionStatusHealthSource;
  selected?: string[];
  small?: boolean;
  onClick?: (partitionName: string) => void;
  onSelect?: (selection: string[]) => void;
  splitPartitions?: boolean;
  hideStatusTooltip?: boolean;
  tooltipMessage?: string;
  selectionWindowSize?: number;
}

export const PartitionStatus = React.memo(
  ({
    partitionNames,
    selected,
    onSelect,
    onClick,
    small,
    health,
    selectionWindowSize,
    hideStatusTooltip,
    tooltipMessage,
    splitPartitions = false,
  }: PartitionStatusProps) => {
    const ref = React.useRef<HTMLDivElement>(null);
    const {viewport, containerProps} = useViewport();

    // Use shared drag selection logic
    const {currentSelectionRange, selectedSpans, handleMouseDown} = usePartitionDragSelection({
      partitionKeys: partitionNames,
      selected,
      onSelect,
      containerRef: ref,
    });

    const segments = useColorSegments(health, splitPartitions, partitionNames);

    const highestIndex = segments
      .map((s) => s.end.idx)
      .reduce((prev, cur) => Math.max(prev, cur), 0);
    const indexToPct = (idx: number) => `${((idx * 100) / partitionNames.length).toFixed(3)}%`;
    const showSeparators =
      splitPartitions && viewport.width > MIN_PARTITION_SPAN_WIDTH * (partitionNames.length + 1);

    const _onClick = onClick
      ? (e: React.MouseEvent<any, MouseEvent>) => {
          const percentage =
            (e.nativeEvent.clientX - (ref.current?.getBoundingClientRect().left || 0)) /
            (ref.current?.clientWidth || 1);
          const partitionName = partitionNames[Math.floor(percentage * partitionNames.length)];
          if (partitionName) {
            onClick(partitionName);
          }
        }
      : undefined;

    const height = small ? 14 : 24;
    const heightPx = `${height}px`;

    return (
      <div
        {...containerProps}
        onMouseDown={(e) => e.preventDefault()}
        onDragStart={(e) => e.preventDefault()}
      >
        {selected && !selectionWindowSize ? (
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
          className={clsx(
            styles.partitionSpansContainer,
            small && styles.partitionSpansContainerSmall,
          )}
          style={{'--height': heightPx} as React.CSSProperties}
          ref={ref}
          onClick={_onClick}
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
              {hideStatusTooltip || tooltipMessage ? (
                <div className={styles.colorSpan} style={s.style} title={tooltipMessage} />
              ) : (
                <Tooltip
                  display="block"
                  position="top"
                  content={
                    tooltipMessage
                      ? tooltipMessage
                      : s.start.idx === s.end.idx
                        ? `Partition ${partitionNames[s.start.idx]} is ${s.label.toLowerCase()}`
                        : `Partitions ${partitionNames[s.start.idx]} through ${
                            partitionNames[s.end.idx]
                          } are ${s.label.toLowerCase()}`
                  }
                >
                  <div className={styles.colorSpan} style={s.style} />
                </Tooltip>
              )}
            </div>
          ))}
          {showSeparators
            ? segments.slice(1).map((s) => (
                <div
                  className={styles.separator}
                  key={`separator_${s.start.idx}`}
                  style={{
                    left: `min(calc(100% - 2px), ${indexToPct(s.start.idx)})`,
                    height,
                  }}
                />
              ))
            : null}
          {currentSelectionRange ? (
            <div
              className={clsx(
                styles.selectionHoverHighlight,
                small && styles.selectionHoverHighlightSmall,
              )}
              style={{
                left: `min(calc(100% - 2px), ${indexToPct(
                  Math.min(
                    partitionNames.indexOf(currentSelectionRange.start),
                    partitionNames.indexOf(currentSelectionRange.end),
                  ),
                )})`,
                width: indexToPct(
                  Math.abs(
                    partitionNames.indexOf(currentSelectionRange.end) -
                      partitionNames.indexOf(currentSelectionRange.start),
                  ) + 1,
                ),
              }}
            />
          ) : null}
          {selected && selected.length && selectionWindowSize ? (
            <>
              <div
                className={styles.selectionFade}
                key="selectionFadeLeft"
                style={{
                  left: 0,
                  width: indexToPct(
                    Math.min(
                      partitionNames.indexOf(
                        assertExists(selected[selected.length - 1], 'Expected non-empty selection'),
                      ),
                      partitionNames.indexOf(
                        assertExists(selected[0], 'Expected non-empty selection'),
                      ),
                    ),
                  ),
                  height,
                }}
              />
              <div
                className={styles.selectionBorder}
                style={{
                  left: `min(calc(100% - 3px), ${indexToPct(
                    Math.min(
                      partitionNames.indexOf(
                        assertExists(selected[0], 'Expected non-empty selection'),
                      ),
                      partitionNames.indexOf(
                        assertExists(selected[selected.length - 1], 'Expected non-empty selection'),
                      ),
                    ),
                  )})`,
                  width: indexToPct(
                    Math.abs(
                      partitionNames.indexOf(
                        assertExists(selected[selected.length - 1], 'Expected non-empty selection'),
                      ) -
                        partitionNames.indexOf(
                          assertExists(selected[0], 'Expected non-empty selection'),
                        ),
                    ) + 1,
                  ),
                  height,
                }}
              />
              <div
                className={styles.selectionFade}
                key="selectionFadeRight"
                style={{
                  right: 0,
                  width: indexToPct(
                    partitionNames.length -
                      1 -
                      Math.max(
                        partitionNames.indexOf(
                          assertExists(
                            selected[selected.length - 1],
                            'Expected non-empty selection',
                          ),
                        ),
                        partitionNames.indexOf(
                          assertExists(selected[0], 'Expected non-empty selection'),
                        ),
                      ),
                  ),
                  height,
                }}
              />
            </>
          ) : null}
        </div>
        {!splitPartitions ? (
          <Box
            flex={{justifyContent: 'space-between'}}
            margin={{top: 4}}
            style={{fontSize: '0.8rem', color: Colors.textLight(), minHeight: 17}}
          >
            <span>{partitionNames[0]}</span>
            <span>{partitionNames[partitionNames.length - 1]}</span>
          </Box>
        ) : null}
      </div>
    );
  },
);

// This type is similar to a partition health "Range", but this component is also
// used by backfill UI and backfills can have a wider range of partition states,
// so this type allows the entire enum.
type ColorSegment = {
  start: {idx: number; key: string};
  end: {idx: number; key: string};
  style: React.CSSProperties;
  label: string;
};

function useColorSegments(
  health: PartitionStatusHealthSource,
  splitPartitions: boolean,
  partitionNames: string[],
) {
  const _ranges = 'ranges' in health ? health.ranges : null;
  const _statusForKey =
    'runStatusForPartitionKey' in health ? health.runStatusForPartitionKey : null;

  return useMemo(() => {
    return _statusForKey
      ? opRunStatusToColorRanges(partitionNames, splitPartitions, _statusForKey)
      : _ranges && splitPartitions
        ? splitColorSegments(partitionNames, assetHealthToColorSegments(_ranges))
        : assetHealthToColorSegments(assertExists(_ranges, 'Expected ranges to be defined'));
  }, [splitPartitions, partitionNames, _ranges, _statusForKey]);
}

// If you ask for each partition to be rendered as a separate segment in the UI, we break the
// provided ranges apart into per-partition ranges so that each partition can have a separate tooltip.
//
function splitColorSegments(partitionNames: string[], segments: ColorSegment[]): ColorSegment[] {
  const result: ColorSegment[] = [];
  for (const segment of segments) {
    for (let idx = segment.start.idx; idx <= segment.end.idx; idx++) {
      const key = assertExists(partitionNames[idx], `Expected partition name at index ${idx}`);
      result.push({
        start: {idx, key},
        end: {idx, key},
        label: segment.label,
        style: segment.style,
      });
    }
  }
  return result;
}

function assetHealthToColorSegments(ranges: Range[]) {
  return ranges.map((range) => ({
    start: range.start,
    end: range.end,
    label: range.value.map((v) => assetPartitionStatusToText(v)).join(', '),
    style: assetPartitionStatusesToStyle(range.value),
  }));
}

const statusToBackgroundColor = (status: RunStatus | undefined) => {
  if (status === undefined) {
    return Colors.backgroundDisabled();
  }
  return status === RunStatus.NOT_STARTED ? Colors.backgroundDisabled() : RUN_STATUS_COLORS[status];
};

function opRunStatusToColorRanges(
  partitionNames: string[],
  splitPartitions: boolean,
  runStatusForKey: (partitionKey: string, partitionIdx: number) => RunStatus | undefined,
) {
  const spans = splitPartitions
    ? partitionNames.map((name, idx) => ({
        startIdx: idx,
        endIdx: idx,
        status: runStatusForKey(name, idx),
      }))
    : assembleIntoSpans(partitionNames, runStatusForKey);

  return spans.map((s) => {
    const label = s.status ? runStatusToBackfillStateString(s.status) : 'Unknown';
    return {
      label,
      start: {idx: s.startIdx, key: partitionNames[s.startIdx]},
      end: {idx: s.endIdx, key: partitionNames[s.endIdx]},
      style: {
        background: statusToBackgroundColor(s.status),
      },
    };
  });
}
