import {Box, Tooltip, Colors, useViewport} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {
  assetPartitionStatusToText,
  assetPartitionStatusesToStyle,
} from '../assets/AssetPartitionStatus';
import {Range} from '../assets/usePartitionHealthData';
import {RunStatus} from '../graphql/types';
import {runStatusToBackfillStateString, RUN_STATUS_COLORS} from '../runs/RunStatusTag';

import {assembleIntoSpans} from './SpanRepresentation';

type SelectionRange = {
  start: string;
  end: string;
};

const MIN_SPAN_WIDTH = 8;

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
  runStatusForPartitionKey: (partitionKey: string, partitionIdx: number) => RunStatus;
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

export const PartitionStatus: React.FC<PartitionStatusProps> = ({
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
}) => {
  const ref = React.useRef<HTMLDivElement>(null);
  const [currentSelectionRange, setCurrentSelectionRange] = React.useState<
    SelectionRange | undefined
  >();
  const {viewport, containerProps} = useViewport();

  const segments = useColorSegments(health, splitPartitions, partitionNames);

  const toPartitionName = React.useCallback(
    (e: MouseEvent) => {
      if (!ref.current) {
        return null;
      }
      const percentage =
        (e.clientX - ref.current.getBoundingClientRect().left) / ref.current.clientWidth;
      return partitionNames[Math.floor(percentage * partitionNames.length)];
    },
    [partitionNames, ref],
  );
  const getRangeSelection = React.useCallback(
    (start: string, end: string) => {
      const startIdx = partitionNames.indexOf(start);
      const endIdx = partitionNames.indexOf(end);
      return partitionNames.slice(Math.min(startIdx, endIdx), Math.max(startIdx, endIdx) + 1);
    },
    [partitionNames],
  );

  const selectedSet = React.useMemo(() => new Set(selected), [selected]);

  React.useEffect(() => {
    if (!currentSelectionRange || !onSelect || !selected) {
      return;
    }
    const onMouseMove = (e: MouseEvent) => {
      const end = toPartitionName(e) || currentSelectionRange.end;
      setCurrentSelectionRange({start: currentSelectionRange?.start, end});
    };
    const onMouseUp = (e: MouseEvent) => {
      if (!currentSelectionRange) {
        return;
      }
      const end = toPartitionName(e) || currentSelectionRange.end;
      const currentSelection = getRangeSelection(currentSelectionRange.start, end);

      const operation = !e.getModifierState('Shift')
        ? 'replace'
        : currentSelection.every((name) => selectedSet.has(name))
        ? 'subtract'
        : 'add';

      if (operation === 'replace') {
        onSelect(currentSelection);
      } else if (operation === 'subtract') {
        onSelect(selected.filter((x) => !currentSelection.includes(x)));
      } else if (operation === 'add') {
        onSelect(Array.from(new Set([...selected, ...currentSelection])));
      }
      setCurrentSelectionRange(undefined);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [onSelect, selected, selectedSet, currentSelectionRange, getRangeSelection, toPartitionName]);

  const selectedSpans = React.useMemo(
    () =>
      selectedSet.size === 0
        ? []
        : selectedSet.size === partitionNames.length
        ? [{startIdx: 0, endIdx: partitionNames.length - 1, status: true}]
        : assembleIntoSpans(partitionNames, (key) => selectedSet.has(key)).filter((s) => s.status),
    [selectedSet, partitionNames],
  );

  const highestIndex = segments.map((s) => s.end.idx).reduce((prev, cur) => Math.max(prev, cur), 0);
  const indexToPct = (idx: number) => `${((idx * 100) / partitionNames.length).toFixed(3)}%`;
  const showSeparators =
    splitPartitions && viewport.width > MIN_SPAN_WIDTH * (partitionNames.length + 1);

  const _onClick = onClick
    ? (e: React.MouseEvent<any, MouseEvent>) => {
        const partitionName = toPartitionName(e.nativeEvent);
        partitionName && onClick(partitionName);
      }
    : undefined;

  const _onMouseDown = onSelect
    ? (e: React.MouseEvent<any, MouseEvent>) => {
        const partitionName = toPartitionName(e.nativeEvent);
        partitionName && setCurrentSelectionRange({start: partitionName, end: partitionName});
      }
    : undefined;

  return (
    <div
      {...containerProps}
      onMouseDown={(e) => e.preventDefault()}
      onDragStart={(e) => e.preventDefault()}
    >
      {selected && !selectionWindowSize ? (
        <SelectionSpansContainer>
          {selectedSpans.map((s) => (
            <div
              className="selection-span"
              key={s.startIdx}
              style={{
                left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
                width: indexToPct(s.endIdx - s.startIdx + 1),
              }}
            />
          ))}
        </SelectionSpansContainer>
      ) : null}
      <PartitionSpansContainer
        style={{height: small ? 12 : 24}}
        ref={ref}
        onClick={_onClick}
        onMouseDown={_onMouseDown}
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
              <div className="color-span" style={s.style} title={tooltipMessage} />
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
                <div className="color-span" style={s.style} />
              </Tooltip>
            )}
          </div>
        ))}
        {showSeparators
          ? segments.slice(1).map((s) => (
              <div
                className="separator"
                key={`separator_${s.start.idx}`}
                style={{
                  left: `min(calc(100% - 2px), ${indexToPct(s.start.idx)})`,
                  height: small ? 14 : 24,
                }}
              />
            ))
          : null}
        {currentSelectionRange ? (
          <SelectionHoverHighlight
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
              height: small ? 14 : 24,
            }}
          />
        ) : null}
        {selected && selected.length && selectionWindowSize ? (
          <>
            <SelectionFade
              key="selectionFadeLeft"
              style={{
                left: 0,
                width: indexToPct(
                  Math.min(
                    partitionNames.indexOf(selected[selected.length - 1]),
                    partitionNames.indexOf(selected[0]),
                  ),
                ),
                height: small ? 14 : 24,
              }}
            />
            <SelectionBorder
              style={{
                left: `min(calc(100% - 3px), ${indexToPct(
                  Math.min(
                    partitionNames.indexOf(selected[0]),
                    partitionNames.indexOf(selected[selected.length - 1]),
                  ),
                )})`,
                width: indexToPct(
                  Math.abs(
                    partitionNames.indexOf(selected[selected.length - 1]) -
                      partitionNames.indexOf(selected[0]),
                  ) + 1,
                ),
                height: small ? 14 : 24,
              }}
            />
            <SelectionFade
              key="selectionFadeRight"
              style={{
                right: 0,
                width: indexToPct(
                  partitionNames.length -
                    1 -
                    Math.max(
                      partitionNames.indexOf(selected[selected.length - 1]),
                      partitionNames.indexOf(selected[0]),
                    ),
                ),
                height: small ? 14 : 24,
              }}
            />
          </>
        ) : null}
      </PartitionSpansContainer>
      {!splitPartitions ? (
        <Box
          flex={{justifyContent: 'space-between'}}
          margin={{top: 4}}
          style={{fontSize: '0.8rem', color: Colors.Gray500, minHeight: 17}}
        >
          <span>{partitionNames[0]}</span>
          <span>{partitionNames[partitionNames.length - 1]}</span>
        </Box>
      ) : null}
    </div>
  );
};

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

  return React.useMemo(() => {
    return _statusForKey
      ? opRunStatusToColorRanges(partitionNames, splitPartitions, _statusForKey)
      : _ranges && splitPartitions
      ? splitColorSegments(partitionNames, assetHealthToColorSegments(_ranges))
      : assetHealthToColorSegments(_ranges!);
  }, [splitPartitions, partitionNames, _ranges, _statusForKey]);
}

// If you ask for each partition to be rendered as a separate segment in the UI, we break the
// provided ranges apart into per-partition ranges so that each partition can have a separate tooltip.
//
function splitColorSegments(partitionNames: string[], segments: ColorSegment[]): ColorSegment[] {
  const result: ColorSegment[] = [];
  for (const segment of segments) {
    for (let idx = segment.start.idx; idx <= segment.end.idx; idx++) {
      result.push({
        start: {idx, key: partitionNames[idx]},
        end: {idx, key: partitionNames[idx]},
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

function opRunStatusToColorRanges(
  partitionNames: string[],
  splitPartitions: boolean,
  runStatusForKey: (partitionKey: string, partitionIdx: number) => RunStatus,
) {
  const spans = splitPartitions
    ? partitionNames.map((name, idx) => ({
        startIdx: idx,
        endIdx: idx,
        status: runStatusForKey(name, idx),
      }))
    : assembleIntoSpans(partitionNames, runStatusForKey);

  return spans.map((s) => ({
    label: runStatusToBackfillStateString(s.status),
    start: {idx: s.startIdx, key: partitionNames[s.startIdx]},
    end: {idx: s.endIdx, key: partitionNames[s.endIdx]},
    style: {
      background: s.status === RunStatus.NOT_STARTED ? Colors.Gray200 : RUN_STATUS_COLORS[s.status],
    },
  }));
}

const SelectionSpansContainer = styled.div`
  position: relative;
  width: 100%;
  overflow-x: hidden;
  height: 10px;

  .selection-span {
    position: absolute;
    top: 0;
    height: 8px;
    border: 2px solid ${Colors.Blue500};
    border-bottom: 0;
  }
`;

const PartitionSpansContainer = styled.div`
  position: relative;
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
  cursor: col-resize;
  background: ${Colors.Gray200};

  .color-span {
    width: 100%;
    height: 24px;
    outline: none;
  }

  .separator {
    width: 1px;
    position: absolute;
    z-index: 4;
    background: ${Colors.KeylineGray};
    top: 0;
  }
`;

const SelectionFade = styled.div`
  position: absolute;
  z-index: 5;
  background: ${Colors.White};
  opacity: 0.5;
  top: 0;
`;

const SelectionHoverHighlight = styled.div`
  min-width: 2px;
  position: absolute;
  z-index: 4;
  background: ${Colors.White};
  opacity: 0.7;
  top: 0;
`;

const SelectionBorder = styled.div`
  min-width: 2px;
  position: absolute;
  z-index: 5;
  border: 3px solid ${Colors.Dark};
  border-radius: 4px;
  top: 0;
`;
