import {Box, Tooltip, Colors} from '@dagster-io/ui';
import * as React from 'react';

import {useViewport} from '../gantt/useViewport';
import {RunStatus} from '../types/globalTypes';

import {assembleIntoSpans} from './PartitionRangeInput';

type SelectionRange = {
  start: string;
  end: string;
};

const MIN_SPAN_WIDTH = 8;

export const PartitionStatus: React.FC<{
  partitionNames: string[];
  partitionData: {[name: string]: RunStatus | null};
  selected?: string[];
  small?: boolean;
  onClick?: (partitionName: string) => void;
  onSelect?: (selection: string[]) => void;
  splitPartitions?: boolean;
  hideStatusTooltip?: boolean;
  tooltipMessage?: string;
  selectionWindowSize?: number;
}> = ({
  partitionNames,
  partitionData,
  selected,
  onSelect,
  onClick,
  splitPartitions,
  small,
  selectionWindowSize,
  hideStatusTooltip,
  tooltipMessage,
}) => {
  const ref = React.useRef<HTMLDivElement>(null);
  const [currentSelectionRange, setCurrentSelectionRange] = React.useState<
    SelectionRange | undefined
  >();
  const {viewport, containerProps} = useViewport();

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

  React.useEffect(() => {
    if (!currentSelectionRange || !onSelect || !selected) {
      return;
    }
    const setHoveredSelectionRange = (e: MouseEvent) => {
      const end = toPartitionName(e) || currentSelectionRange.end;
      setCurrentSelectionRange({start: currentSelectionRange?.start, end});
    };
    const setSelectionRange = (e: MouseEvent) => {
      if (!currentSelectionRange) {
        return;
      }
      const end = toPartitionName(e);
      const currentSelection = getRangeSelection(
        currentSelectionRange.start,
        end || currentSelectionRange.end,
      );
      const allSelected = currentSelection.every((name) => selected.includes(name));
      if (allSelected) {
        onSelect(selected.filter((x) => !currentSelection.includes(x)));
      } else {
        const newSelected = new Set(selected);
        currentSelection.forEach((name) => newSelected.add(name));
        onSelect(Array.from(newSelected));
      }
      setCurrentSelectionRange(undefined);
    };
    window.addEventListener('mousemove', setHoveredSelectionRange);
    window.addEventListener('mouseup', setSelectionRange);
    return () => {
      window.removeEventListener('mousemove', setHoveredSelectionRange);
      window.removeEventListener('mouseup', setSelectionRange);
    };
  }, [onSelect, selected, currentSelectionRange, getRangeSelection, toPartitionName]);

  const selectedSpans = selected
    ? assembleIntoSpans(partitionNames, (key) => selected.includes(key)).filter((s) => s.status)
    : [];
  const spans = splitPartitions
    ? partitionNames.map((name, idx) => ({startIdx: idx, endIdx: idx, status: partitionData[name]}))
    : _partitionsToSpans(partitionNames, partitionData);
  const highestIndex = spans.map((s) => s.endIdx).reduce((prev, cur) => Math.max(prev, cur), 0);
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
        const name = toPartitionName(e.nativeEvent);
        if (!name) {
          return;
        }
        setCurrentSelectionRange({start: name, end: name});
      }
    : undefined;

  return (
    <div {...containerProps}>
      {selected && !selectionWindowSize ? (
        <div style={{position: 'relative', width: '100%', overflowX: 'hidden', height: 10}}>
          {selectedSpans.map((s) => (
            <div
              key={s.startIdx}
              style={{
                left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
                width: indexToPct(s.endIdx - s.startIdx + 1),
                position: 'absolute',
                top: 0,
                height: 8,
                border: `2px solid ${Colors.Blue500}`,
                borderBottom: 0,
              }}
            />
          ))}
        </div>
      ) : null}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: small ? 12 : 24,
          borderRadius: 4,
          overflow: 'hidden',
          cursor: 'pointer',
        }}
        ref={ref}
        onClick={_onClick}
        onMouseDown={_onMouseDown}
      >
        {spans.map((s) => (
          <div
            key={s.startIdx}
            style={{
              left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
              width: indexToPct(s.endIdx - s.startIdx + 1),
              minWidth: s.status ? 2 : undefined,
              position: 'absolute',
              zIndex: s.startIdx === 0 || s.endIdx === highestIndex ? 3 : s.status ? 2 : 1, //End-caps, then statuses, then missing
              top: 0,
            }}
          >
            {hideStatusTooltip || tooltipMessage ? (
              <div
                style={{
                  width: '100%',
                  height: 24,
                  outline: 'none',
                  background: _statusToColor(s.status),
                }}
                title={tooltipMessage}
              />
            ) : (
              <Tooltip
                display="block"
                content={
                  tooltipMessage
                    ? tooltipMessage
                    : s.startIdx === s.endIdx
                    ? `Partition ${partitionNames[s.startIdx]} is ${_statusToText(s.status)}`
                    : `Partitions ${partitionNames[s.startIdx]} through ${
                        partitionNames[s.endIdx]
                      } are ${_statusToText(s.status)}`
                }
              >
                <div
                  style={{
                    width: '100%',
                    height: 24,
                    outline: 'none',
                    background: _statusToColor(s.status),
                  }}
                />
              </Tooltip>
            )}
          </div>
        ))}
        {showSeparators
          ? spans.slice(1).map((s) => (
              <div
                key={`separator_${s.startIdx}`}
                style={{
                  left: `min(calc(100% - 2px), ${indexToPct(s.startIdx)})`,
                  width: 1,
                  height: small ? 14 : 24,
                  position: 'absolute',
                  zIndex: 4,
                  background: Colors.KeylineGray,
                  top: 0,
                }}
              />
            ))
          : null}
        {currentSelectionRange ? (
          <div
            key="currentSelectionRange"
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
              minWidth: 2,
              height: small ? 14 : 24,
              position: 'absolute',
              zIndex: 4,
              background: Colors.White,
              opacity: 0.7,
              top: 0,
            }}
          />
        ) : null}
        {selected && selected.length && selectionWindowSize ? (
          <>
            <div
              key="selectionRangeBackgroundLeft"
              style={{
                left: 0,
                width: indexToPct(
                  Math.min(
                    partitionNames.indexOf(selected[selected.length - 1]),
                    partitionNames.indexOf(selected[0]),
                  ),
                ),
                height: small ? 14 : 24,
                position: 'absolute',
                zIndex: 5,
                background: Colors.White,
                opacity: 0.5,
                top: 0,
              }}
            />
            <div
              key="selectionRange"
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
                minWidth: 2,
                height: small ? 14 : 24,
                position: 'absolute',
                zIndex: 5,
                border: `3px solid ${Colors.Dark}`,
                borderRadius: 4,
                top: 0,
              }}
            />
            <div
              key="selectionRangeBackgroundRight"
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
                position: 'absolute',
                zIndex: 5,
                background: Colors.White,
                opacity: 0.5,
                top: 0,
              }}
            />
          </>
        ) : null}
      </div>
      {!splitPartitions ? (
        <Box
          flex={{justifyContent: 'space-between'}}
          margin={{top: 4}}
          style={{fontSize: '0.8rem', color: Colors.Gray500}}
        >
          <span>{partitionNames[0]}</span>
          <span>{partitionNames[partitionNames.length - 1]}</span>
        </Box>
      ) : null}
    </div>
  );
};

function _partitionsToSpans(keys: string[], keyStatus: {[key: string]: RunStatus | null}) {
  const spans: {startIdx: number; endIdx: number; status: RunStatus | null}[] = [];

  for (let ii = 0; ii < keys.length; ii++) {
    const status: RunStatus | null = keys[ii] in keyStatus ? keyStatus[keys[ii]] : null;
    if (!spans.length || spans[spans.length - 1].status !== status) {
      spans.push({startIdx: ii, endIdx: ii, status});
    } else {
      spans[spans.length - 1].endIdx = ii;
    }
  }

  return spans;
}

const _statusToColor = (status: RunStatus | null) => {
  switch (status) {
    case RunStatus.SUCCESS:
      return Colors.Green500;
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
    case RunStatus.FAILURE:
      return Colors.Red500;
    case RunStatus.STARTED:
      return Colors.Blue500;
    case RunStatus.QUEUED:
      return Colors.Blue200;
    default:
      return Colors.Gray200;
  }
};

const _statusToText = (status: RunStatus | null) => {
  switch (status) {
    case RunStatus.SUCCESS:
      return 'complete';
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
    case RunStatus.FAILURE:
      return 'failed';
    case RunStatus.STARTED:
      return 'in progress';
    case RunStatus.QUEUED:
      return 'queued';
    default:
      return 'missing';
  }
};
