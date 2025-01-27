import {
  Box,
  Colors,
  FontFamily,
  Icon,
  MiddleTruncate,
  Mono,
  Popover,
  Row,
  Spinner,
  Tag,
  Tooltip,
  useViewport,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {RunStatusDot} from './RunStatusDots';
import {failedStatuses, inProgressStatuses, successStatuses} from './RunStatuses';
import {RunTimelineRowIcon} from './RunTimelineRowIcon';
import {RowObjectType, TimelineRow, TimelineRun} from './RunTimelineTypes';
import {TimeElapsed} from './TimeElapsed';
import {RunBatch, batchRunsForTimeline} from './batchRunsForTimeline';
import {mergeStatusToBackground} from './mergeStatusToBackground';
import {COMMON_COLLATOR} from '../app/Util';
import {OVERVIEW_COLLAPSED_KEY} from '../overview/OverviewExpansionKey';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {AnchorButton} from '../ui/AnchorButton';
import {Container, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useFormatDateTime} from '../ui/useFormatDateTime';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {SECTION_HEADER_HEIGHT} from '../workspace/TableSectionHeader';
import {RepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';
import {RepoAddress} from '../workspace/types';

const ROW_HEIGHT = 32;
const TIME_HEADER_HEIGHT = 32;
const DATE_TIME_HEIGHT = TIME_HEADER_HEIGHT * 2;
const EMPTY_STATE_HEIGHT = 110;
const LEFT_SIDE_SPACE_ALLOTTED = 320;
const LABEL_WIDTH = 268;
const MIN_DATE_WIDTH_PCT = 10;

const ONE_HOUR_MSEC = 60 * 60 * 1000;

export const CONSTANTS = {
  ROW_HEIGHT,
  DATE_TIME_HEIGHT,
  TIME_HEADER_HEIGHT,
  ONE_HOUR_MSEC,
  EMPTY_STATE_HEIGHT,
  LEFT_SIDE_SPACE_ALLOTTED,
};

const SORT_PRIORITY: Record<RowObjectType, number> = {
  asset: 0,
  manual: 0,
  'legacy-amp': 0,
  schedule: 1,
  sensor: 1,
  job: 2,
};

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; rowCount: number}
  | {type: RowObjectType; repoAddress: RepoAddress; row: TimelineRow};

interface Props {
  loading?: boolean;
  rows: TimelineRow[];
  rangeMs: [number, number];
}

export const RunTimeline = (props: Props) => {
  const {loading = false, rows, rangeMs} = props;
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const {
    viewport: {width},
    containerProps: {ref: measureRef},
  } = useViewport();

  const now = Date.now();
  const [_, end] = rangeMs;
  const includesTicks = now <= end;

  const buckets = React.useMemo(
    () =>
      rows.reduce(
        (accum, row) => {
          const {repoAddress} = row;
          const repoKey = repoAddressAsURLString(repoAddress);
          accum[repoKey] = accum[repoKey] || [];
          accum[repoKey]!.push(row);
          return accum;
        },
        {} as Record<string, TimelineRow[]>,
      ),
    [rows],
  );

  const allKeys = Object.keys(buckets);
  const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
    OVERVIEW_COLLAPSED_KEY,
    allKeys,
  );

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    Object.entries(buckets)
      .sort((bucketA, bucketB) => COMMON_COLLATOR.compare(bucketA[0], bucketB[0]))
      .forEach(([repoKey, bucket]) => {
        const repoAddress = repoAddressFromPath(repoKey);
        if (!repoAddress) {
          return;
        }

        flat.push({type: 'header', repoAddress, rowCount: bucket.length});
        if (expandedKeys.includes(repoKey)) {
          bucket
            .sort((a, b) => {
              return (
                SORT_PRIORITY[a.type] - SORT_PRIORITY[b.type] ||
                COMMON_COLLATOR.compare(a.name, b.name)
              );
            })
            .forEach((row) => {
              flat.push({type: row.type, repoAddress, row});
            });
        }
      });

    return flat;
  }, [buckets, expandedKeys]);

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (_: number) => 32,
    overscan: 40,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  if (!width) {
    return <div style={{height: DATE_TIME_HEIGHT + EMPTY_STATE_HEIGHT}} ref={measureRef} />;
  }

  const repoOrder = Object.keys(buckets).sort((a, b) => a.localeCompare(b));

  const expandedRepos = repoOrder.filter((repoKey) => expandedKeys.includes(repoKey));
  const expandedJobCount = expandedRepos.reduce(
    (accum, repoKey) => accum + buckets[repoKey]!.length,
    0,
  );
  const height = repoOrder.length * SECTION_HEADER_HEIGHT + ROW_HEIGHT * expandedJobCount;
  const duplicateRepoNames = findDuplicateRepoNames(
    repoOrder.map((repoKey) => repoAddressFromPath(repoKey)?.name || ''),
  );
  const anyObjects = repoOrder.length > 0;

  return (
    <>
      <div ref={measureRef} />
      <Box
        padding={{left: 24}}
        flex={{direction: 'column', justifyContent: 'center'}}
        style={{fontSize: '16px', flex: `0 0 ${DATE_TIME_HEIGHT}px`}}
        border="top-and-bottom"
      >
        Runs
      </Box>
      <div style={{position: 'relative'}}>
        <TimeDividers interval={ONE_HOUR_MSEC} rangeMs={rangeMs} height={anyObjects ? height : 0} />
      </div>
      {repoOrder.length ? (
        <div style={{overflow: 'hidden', position: 'relative'}}>
          <Container ref={parentRef}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => {
                const row: RowType = flattened[index]!;
                const type = row!.type;
                if (type === 'header') {
                  const repoKey = repoAddressAsURLString(row.repoAddress);
                  const repoName = row.repoAddress.name;
                  return (
                    <TimelineHeaderRow
                      expanded={expandedKeys.includes(repoKey)}
                      key={repoKey}
                      height={size}
                      top={start}
                      repoAddress={row.repoAddress}
                      isDuplicateRepoName={!!(repoName && duplicateRepoNames.has(repoName))}
                      rows={buckets[repoKey]!}
                      onToggle={onToggle}
                      onToggleAll={onToggleAll}
                    />
                  );
                }

                return (
                  <RunTimelineRow
                    row={row.row}
                    key={key}
                    height={size}
                    top={start}
                    rangeMs={rangeMs}
                    width={width}
                  />
                );
              })}
            </Inner>
          </Container>
        </div>
      ) : (
        <RunsEmptyOrLoading loading={loading} includesTicks={includesTicks} />
      )}
    </>
  );
};

interface TimelineHeaderRowProps {
  expanded: boolean;
  repoAddress: RepoAddress;
  isDuplicateRepoName: boolean;
  rows: TimelineRow[];
  height: number;
  top: number;
  onToggle: (repoAddress: RepoAddress) => void;
  onToggleAll: (expanded: boolean) => void;
}

const TimelineHeaderRow = (props: TimelineHeaderRowProps) => {
  const {expanded, onToggle, onToggleAll, repoAddress, isDuplicateRepoName, rows, height, top} =
    props;

  return (
    <RepoRow
      expanded={expanded}
      height={height}
      start={top}
      repoAddress={repoAddress}
      showLocation={isDuplicateRepoName}
      onToggle={onToggle}
      onToggleAll={onToggleAll}
      rightElement={<RunStatusTags rows={rows} />} // todo dish: Fix this
    />
  );
};

const RunStatusTags = React.memo(({rows}: {rows: TimelineRow[]}) => {
  const counts = React.useMemo(() => {
    let inProgressCount = 0;
    let failedCount = 0;
    let succeededCount = 0;
    rows.forEach(({runs}) => {
      runs.forEach(({status}) => {
        // Refine `SCHEDULED` out so that our Set checks below pass TypeScript.
        if (status === 'SCHEDULED') {
          return;
        }
        if (inProgressStatuses.has(status)) {
          inProgressCount++;
        } else if (failedStatuses.has(status)) {
          failedCount++;
        } else if (successStatuses.has(status)) {
          succeededCount++;
        }
      });
    });
    return {inProgressCount, failedCount, succeededCount};
  }, [rows]);

  return <RunStatusTagsWithCounts {...counts} />;
});

export const RunStatusTagsWithCounts = ({
  inProgressCount,
  succeededCount,
  failedCount,
}: {
  inProgressCount: number;
  succeededCount: number;
  failedCount: number;
}) => {
  const inProgressText =
    inProgressCount === 1 ? '1 run in progress' : `${inProgressCount} runs in progress`;
  const succeededText =
    succeededCount === 1 ? '1 run succeeded' : `${succeededCount} runs succeeded`;
  const failedText = failedCount === 1 ? '1 run failed' : `${failedCount} runs failed`;

  return (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      {inProgressCount > 0 ? (
        <Tooltip content={<StatusSpan>{inProgressText}</StatusSpan>} placement="top">
          <Tag intent="primary">{inProgressCount}</Tag>
        </Tooltip>
      ) : null}
      {succeededCount > 0 ? (
        <Tooltip content={<StatusSpan>{succeededText}</StatusSpan>} placement="top">
          <Tag intent="success">{succeededCount}</Tag>
        </Tooltip>
      ) : null}
      {failedCount > 0 ? (
        <Tooltip content={<StatusSpan>{failedText}</StatusSpan>} placement="top">
          <Tag intent="danger">{failedCount}</Tag>
        </Tooltip>
      ) : null}
    </Box>
  );
};

const StatusSpan = styled.span`
  white-space: nowrap;
`;

type DateMarker = {
  key: string;
  label: React.ReactNode;
  left: number;
  width: number;
};

type TimeMarker = {
  key: string;
  label: React.ReactNode;
  left: number;
};

interface TimeDividersProps {
  height: number;
  interval: number;
  rangeMs: [number, number];
  annotations?: {label: string; ms: number}[];
  now?: number;
}

const dateTimeOptions: Intl.DateTimeFormatOptions = {
  month: 'numeric',
  day: 'numeric',
  year: 'numeric',
};

const dateTimeOptionsWithTimezone: Intl.DateTimeFormatOptions = {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZoneName: 'short',
};

const timeOnlyOptionsWithMinute: Intl.DateTimeFormatOptions = {
  hour: 'numeric',
  minute: 'numeric',
};

const timeOnlyOptions: Intl.DateTimeFormatOptions = {
  hour: 'numeric',
};

export const TimeDividers = (props: TimeDividersProps) => {
  const {interval, rangeMs, annotations, height, now: _now} = props;
  const [start, end] = rangeMs;
  const formatDateTime = useFormatDateTime();

  // Create a cursor date at midnight in the user's timezone, to be used when
  // generating date and time markers.
  const boundaryCursor = useMemo(() => {
    const startDate = new Date(start);
    const startDateStringWithTimezone = formatDateTime(
      startDate,
      dateTimeOptionsWithTimezone,
      'en-US',
    );
    return new Date(startDateStringWithTimezone);
  }, [formatDateTime, start]);

  const dateMarkers: DateMarker[] = React.useMemo(() => {
    const totalTime = end - start;
    const dayBoundaries = [];

    let cursor = boundaryCursor;

    // Add date boundaries. This is not identical to time interval boundaries, due to
    // daylight savings.
    while (cursor.valueOf() < end) {
      const dayStart = cursor.getTime();
      const dayEnd = new Date(dayStart).setDate(cursor.getDate() + 1); // Increment by one day.
      cursor = new Date(dayEnd);
      dayBoundaries.push({dayStart, dayEnd});
    }

    return dayBoundaries.map(({dayStart, dayEnd}) => {
      const date = new Date(dayStart);
      const startLeftMsec = dayStart - start;
      const dayLength = dayEnd - dayStart; // This can vary with DST
      const endRight = startLeftMsec + dayLength;

      const left = Math.max(0, (startLeftMsec / totalTime) * 100);
      const right = Math.min(100, (endRight / totalTime) * 100);

      return {
        label: formatDateTime(date, dateTimeOptions),
        key: date.toString(),
        left,
        width: right - left,
      };
    });
  }, [boundaryCursor, end, formatDateTime, start]);

  const timeMarkers: TimeMarker[] = React.useMemo(() => {
    const totalTime = end - start;
    const timeBoundaries = [];

    let cursor = boundaryCursor;

    // Add time boundaries at every interval.
    while (cursor.valueOf() < end) {
      const intervalStart = cursor.getTime();
      const intervalEnd = new Date(intervalStart).setTime(cursor.getTime() + interval); // Increment by interval.
      cursor = new Date(intervalEnd);
      timeBoundaries.push(intervalStart);
    }

    // Create boundary markers, then slice off any markers that would be offscreen.
    return timeBoundaries
      .map((intervalStart) => {
        const date = new Date(intervalStart);
        const startLeftMsec = intervalStart - start;
        const left = Math.max(0, (startLeftMsec / totalTime) * 100);
        const label =
          interval < ONE_HOUR_MSEC
            ? formatDateTime(date, timeOnlyOptionsWithMinute).replace(' ', '')
            : formatDateTime(date, timeOnlyOptions).replace(' ', '');

        return {
          label,
          key: date.toString(),
          left,
        };
      })
      .filter((marker) => marker.left > 0);
  }, [end, start, boundaryCursor, interval, formatDateTime]);

  const now = _now || Date.now();
  const msToLeft = (ms: number) => `${(((ms - start) / (end - start)) * 100).toPrecision(3)}%`;

  return (
    <DividerContainer style={{height: `${height}px`, top: `-${DATE_TIME_HEIGHT}px`}}>
      <DividerLabels>
        {dateMarkers.map((marker) => (
          <DateLabel
            key={marker.key}
            style={{
              left: `${marker.left.toPrecision(3)}%`,
              width: `${marker.width.toPrecision(3)}%`,
            }}
          >
            {marker.width > MIN_DATE_WIDTH_PCT ? (
              <Box flex={{justifyContent: 'center'}}>{marker.label}</Box>
            ) : null}
          </DateLabel>
        ))}
      </DividerLabels>
      <DividerLabels>
        {timeMarkers.map((marker) => (
          <TimeLabel key={marker.key} style={{left: `${marker.left.toPrecision(3)}%`}}>
            {marker.label}
          </TimeLabel>
        ))}
      </DividerLabels>
      <DividerLines>
        <DividerLine style={{left: 0, backgroundColor: Colors.keylineDefault()}} />
        {timeMarkers.map((marker) => (
          <DividerLine key={marker.key} style={{left: `${marker.left.toPrecision(3)}%`}} />
        ))}
        {now >= start && now <= end ? (
          <>
            <TimlineMarker style={{left: msToLeft(now)}}>Now</TimlineMarker>
            <DividerLine
              style={{left: msToLeft(now), backgroundColor: Colors.accentPrimary(), zIndex: 1}}
            />
          </>
        ) : null}
        {(annotations || [])
          .filter((annotation) => annotation.ms >= start && annotation.ms <= end)
          .map((annotation) => (
            <React.Fragment key={annotation.label}>
              <TimlineMarker style={{left: msToLeft(annotation.ms)}}>
                {annotation.label}
              </TimlineMarker>
              <DividerLine
                style={{
                  left: msToLeft(annotation.ms),
                  backgroundColor: Colors.accentPrimary(),
                  zIndex: 1,
                }}
              />
            </React.Fragment>
          ))}
      </DividerLines>
    </DividerContainer>
  );
};

const DividerContainer = styled.div`
  position: absolute;
  top: 0;
  left: ${LEFT_SIDE_SPACE_ALLOTTED}px;
  right: 0;
  font-family: ${FontFamily.monospace};
  color: ${Colors.textLighter()};
`;

const DividerLabels = styled.div`
  display: flex;
  align-items: center;
  box-shadow:
    inset 1px 0 0 ${Colors.keylineDefault()},
    inset 0 1px 0 ${Colors.keylineDefault()},
    inset -1px 0 0 ${Colors.keylineDefault()};
  height: ${TIME_HEADER_HEIGHT}px;
  position: relative;
  user-select: none;
  font-size: 12px;
  width: 100%;
  overflow: hidden;

  :first-child {
    box-shadow:
      inset 1px 0 0 ${Colors.keylineDefault()},
      inset -1px 0 0 ${Colors.keylineDefault()};
  }
`;

const DateLabel = styled.div`
  position: absolute;
  padding: 8px 0;
  white-space: nowrap;

  :not(:first-child) {
    box-shadow: inset 1px 0 0 ${Colors.keylineDefault()};
  }
`;

const TimeLabel = styled.div`
  position: absolute;
  padding: 8px;
  box-shadow: inset 1px 0 0 ${Colors.keylineDefault()};
  white-space: nowrap;
`;

const DividerLines = styled.div`
  height: 100%;
  position: relative;
  width: 100%;
  box-shadow:
    inset 1px 0 0 ${Colors.keylineDefault()},
    inset -1px 0 0 ${Colors.keylineDefault()};
`;

const DividerLine = styled.div`
  background-color: ${Colors.keylineDefault()};
  height: 100%;
  position: absolute;
  top: 0;
  width: 1px;
`;

const TimlineMarker = styled.div`
  background-color: ${Colors.accentPrimary()};
  border-radius: 1px;
  color: ${Colors.accentReversed()};
  cursor: default;
  font-size: 10px;
  line-height: 12px;
  transform: translate(-50%, 0);
  padding: 1px 4px;
  position: absolute;
  top: -14px;
  user-select: none;
`;

const MIN_CHUNK_WIDTH = 4;
const MIN_WIDTH_FOR_MULTIPLE = 12;

const RunTimelineRow = ({
  row,
  top,
  height,
  rangeMs,
  width: containerWidth,
}: {
  row: TimelineRow;
  top: number;
  height: number;
  rangeMs: [number, number];
  width: number;
}) => {
  const [start, end] = rangeMs;
  const width = containerWidth - LEFT_SIDE_SPACE_ALLOTTED;
  const {runs} = row;

  // Batch overlapping runs in this row.
  const batched = React.useMemo(() => {
    const batches: RunBatch<TimelineRun>[] = batchRunsForTimeline({
      runs,
      start,
      end,
      width,
      minChunkWidth: MIN_CHUNK_WIDTH,
      minMultipleWidth: MIN_WIDTH_FOR_MULTIPLE,
    });

    return batches;
  }, [runs, start, end, width]);

  if (!row.runs.length) {
    return null;
  }

  return (
    <TimelineRowContainer $height={height} $start={top}>
      <RowName>
        <RunTimelineRowIcon type={row.type} />
        <div style={{width: LABEL_WIDTH}}>
          {row.path ? (
            <Link to={row.path}>
              <MiddleTruncate text={row.name} />
            </Link>
          ) : (
            <span style={{color: Colors.textDefault()}}>
              <MiddleTruncate text={row.name} />
            </span>
          )}
        </div>
      </RowName>
      <RunChunks>
        {batched.map((batch) => {
          const {left, width, runs} = batch;
          const runCount = runs.length;
          return (
            <RunChunk
              key={batch.runs[0]!.id}
              $background={mergeStatusToBackground(batch.runs)}
              $multiple={runCount > 1}
              style={{
                left: `${left}px`,
                width: `${width}px`,
              }}
            >
              <Popover
                content={<RunHoverContent row={row} batch={batch} />}
                position="top"
                interactionKind="hover"
                className="chunk-popover-target"
              >
                <Box
                  flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
                  style={{height: '100%'}}
                >
                  {runCount > 1 ? <BatchCount>{batch.runs.length}</BatchCount> : null}
                </Box>
              </Popover>
            </RunChunk>
          );
        })}
      </RunChunks>
    </TimelineRowContainer>
  );
};

const RunsEmptyOrLoading = (props: {loading: boolean; includesTicks: boolean}) => {
  const {loading, includesTicks} = props;

  const content = () => {
    if (loading) {
      return (
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Spinner purpose="body-text" />
          {includesTicks ? 'Loading runs and scheduled ticks' : 'Loading runs'}
        </Box>
      );
    }

    return (
      <Box flex={{direction: 'column', gap: 12, alignItems: 'center'}}>
        <div>
          {includesTicks
            ? 'No runs or scheduled ticks in this time period.'
            : 'No runs in this time period.'}
        </div>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          <AnchorButton icon={<Icon name="add_circle" />} to="/overview/jobs">
            Launch a run
          </AnchorButton>
          <span>or</span>
          <AnchorButton icon={<Icon name="materialization" />} to="/asset-groups">
            Materialize an asset
          </AnchorButton>
        </Box>
      </Box>
    );
  };

  return (
    <Box
      background={Colors.backgroundDefault()}
      padding={{vertical: 24}}
      flex={{direction: 'row', justifyContent: 'center'}}
      border="top-and-bottom"
    >
      {content()}
    </Box>
  );
};

type RowProps = {$height: number; $start: number};

export const TimelineRowContainer = styled.div.attrs<RowProps>(({$height, $start}) => ({
  style: {
    height: `${$height}px`,
    transform: `translateY(${$start}px)`,
  },
}))<RowProps>`
  align-items: center;
  box-shadow: inset 0 -1px 0 ${Colors.keylineDefault()};
  display: flex;
  flex-direction: row;
  width: 100%;
  padding: 1px 0;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
  overflow: hidden;
  transition: background-color 100ms linear;

  :hover {
    background-color: ${Colors.backgroundDefaultHover()};
  }
`;

const RowName = styled.div`
  align-items: center;
  display: flex;
  font-size: 13px;
  justify-content: flex-start;
  gap: 8px;
  line-height: 16px;
  overflow: hidden;
  padding: 0 12px 0 24px;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: ${LEFT_SIDE_SPACE_ALLOTTED}px;
`;

export const RunChunks = styled.div`
  flex: 1;
  position: relative;
  height: ${ROW_HEIGHT}px;
`;

interface ChunkProps {
  $background: string;
  $multiple: boolean;
}

export const RunChunk = styled.div<ChunkProps>`
  align-items: center;
  background: ${({$background}) => $background};
  border-radius: 1px;
  height: ${ROW_HEIGHT - 8}px;
  position: absolute;
  top: 4px;
  ${({$multiple}) => ($multiple ? `min-width: ${MIN_WIDTH_FOR_MULTIPLE}px` : null)};

  transition:
    background 200ms linear,
    opacity 200ms linear,
    width 200ms ease-in-out;

  :hover {
    opacity: 0.7;
  }
  .chunk-popover-target {
    display: block;
    height: 100%;
    width: 100%;
  }
`;

const BatchCount = styled.div`
  color: ${Colors.accentReversed()};
  cursor: default;
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  font-weight: 600;
  user-select: none;
`;

interface RunHoverContentProps {
  row: TimelineRow;
  batch: RunBatch<TimelineRun>;
}

const RunHoverContent = (props: RunHoverContentProps) => {
  const {row, batch} = props;
  const count = batch.runs.length;
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const virtualizer = useVirtualizer({
    count,
    getScrollElement: () => parentRef.current,
    estimateSize: (_: number) => ROW_HEIGHT,
    overscan: 10,
  });

  const totalHeight = virtualizer.getTotalSize();
  const items = virtualizer.getVirtualItems();
  const height = Math.min(count * ROW_HEIGHT, 240);

  return (
    <Box style={{width: '260px'}}>
      <Box padding={12} border="bottom" flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <RunTimelineRowIcon type={row.type} />
        <HoverContentRowName>{row.name}</HoverContentRowName>
      </Box>
      <div style={{height, overflowY: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const run = batch.runs[index]!;
              return (
                <Row key={key} $height={size} $start={start}>
                  <Box
                    key={key}
                    border={index > 0 ? 'top' : null}
                    flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
                    padding={{vertical: 8, horizontal: 12}}
                  >
                    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                      <RunStatusDot status={run.status} size={8} />
                      {run.status === 'SCHEDULED' ? (
                        'Scheduled'
                      ) : (
                        <Link to={`/runs/${run.id}`}>
                          <Mono>{run.id.slice(0, 8)}</Mono>
                        </Link>
                      )}
                    </Box>
                    <Mono>
                      {run.status === 'SCHEDULED' ? (
                        <TimestampDisplay timestamp={run.startTime / 1000} />
                      ) : (
                        <TimeElapsed
                          startUnix={run.startTime / 1000}
                          endUnix={run.endTime / 1000}
                        />
                      )}
                    </Mono>
                  </Box>
                </Row>
              );
            })}
          </Inner>
        </Container>
      </div>
      {row.path ? (
        <Box padding={12} border="top" flex={{direction: 'row', justifyContent: 'center'}}>
          <Link to={`${row.path}/runs`}>View all</Link>
        </Box>
      ) : null}
    </Box>
  );
};

const HoverContentRowName = styled.strong`
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
`;
