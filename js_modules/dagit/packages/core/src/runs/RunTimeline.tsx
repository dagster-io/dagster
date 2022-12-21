import {
  Box,
  Colors,
  Popover,
  Mono,
  FontFamily,
  Tooltip,
  Tag,
  Icon,
  Spinner,
  MiddleTruncate,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {OVERVIEW_COLLAPSED_KEY} from '../overview/OverviewExpansionKey';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {RunStatus} from '../types/globalTypes';
import {AnchorButton} from '../ui/AnchorButton';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useFormatDateTime} from '../ui/useFormatDateTime';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';
import {RepoAddress} from '../workspace/types';

import {RepoSectionHeader, SECTION_HEADER_HEIGHT} from './RepoSectionHeader';
import {RunStatusDot} from './RunStatusDots';
import {failedStatuses, inProgressStatuses, successStatuses} from './RunStatuses';
import {TimeElapsed} from './TimeElapsed';
import {batchRunsForTimeline, RunBatch} from './batchRunsForTimeline';
import {mergeStatusToBackground} from './mergeStatusToBackground';

const ROW_HEIGHT = 32;
const TIME_HEADER_HEIGHT = 32;
const DATE_TIME_HEIGHT = TIME_HEADER_HEIGHT * 2;
const EMPTY_STATE_HEIGHT = 110;
const LEFT_SIDE_SPACE_ALLOTTED = 320;
const LABEL_WIDTH = 268;
const MIN_DATE_WIDTH_PCT = 10;

const ONE_HOUR_MSEC = 60 * 60 * 1000;

export type TimelineRun = {
  id: string;
  status: RunStatus | 'SCHEDULED';
  startTime: number;
  endTime: number;
};

export type TimelineJob = {
  key: string;
  repoAddress: RepoAddress;
  jobName: string;
  jobType: 'job' | 'asset';
  path: string;
  runs: TimelineRun[];
};

interface Props {
  loading?: boolean;
  jobs: TimelineJob[];
  range: [number, number];
}

export const RunTimeline = (props: Props) => {
  const {loading = false, jobs, range} = props;
  const [width, setWidth] = React.useState<number | null>(null);

  const now = Date.now();
  const [_, end] = range;
  const includesTicks = now <= end;

  const buckets = jobs.reduce((accum, job) => {
    const {repoAddress} = job;
    const repoKey = repoAddressAsURLString(repoAddress);
    const jobsForRepo = accum[repoKey] || [];
    return {...accum, [repoKey]: [...jobsForRepo, job]};
  }, {});

  const allKeys = Object.keys(buckets);
  const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
    OVERVIEW_COLLAPSED_KEY,
    allKeys,
  );

  const observer = React.useRef<ResizeObserver | null>(null);

  const containerRef = React.useCallback((node) => {
    if (node) {
      observer.current = new ResizeObserver((entries) => {
        const entry = entries[0];
        setWidth(entry.contentRect.width);
      });
      observer.current.observe(node);
    } else {
      observer.current?.disconnect();
    }
  }, []);

  if (!width) {
    return (
      <Timeline $height={DATE_TIME_HEIGHT + EMPTY_STATE_HEIGHT} ref={containerRef}>
        <div />
      </Timeline>
    );
  }

  const repoOrder = Object.keys(buckets).sort((a, b) => a.localeCompare(b));

  let nextTop = DATE_TIME_HEIGHT;
  const expandedRepos = repoOrder.filter((repoKey) => expandedKeys.includes(repoKey));
  const expandedJobCount = expandedRepos.reduce(
    (accum, repoKey) => accum + buckets[repoKey].length,
    0,
  );
  const height = repoOrder.length * SECTION_HEADER_HEIGHT + ROW_HEIGHT * expandedJobCount;
  const duplicateRepoNames = findDuplicateRepoNames(
    repoOrder.map((repoKey) => repoAddressFromPath(repoKey)?.name || ''),
  );
  const anyJobs = repoOrder.length > 0;
  const timelineHeight = DATE_TIME_HEIGHT + (anyJobs ? height : EMPTY_STATE_HEIGHT);

  return (
    <Timeline $height={timelineHeight} ref={containerRef}>
      <Box
        padding={{left: 24}}
        flex={{direction: 'column', justifyContent: 'center'}}
        style={{fontSize: '16px', height: DATE_TIME_HEIGHT}}
        border={{side: 'top', width: 1, color: Colors.KeylineGray}}
      >
        Jobs
      </Box>
      <TimeDividers interval={ONE_HOUR_MSEC} range={range} height={anyJobs ? height : 0} />
      {repoOrder.length ? (
        repoOrder.map((repoKey) => {
          const name = repoAddressFromPath(repoKey)?.name;
          const jobs = buckets[repoKey];
          const top = nextTop;
          const expanded = expandedKeys.includes(repoKey);
          nextTop = top + SECTION_HEADER_HEIGHT + (expanded ? jobs.length * ROW_HEIGHT : 0);
          return (
            <TimelineSection
              expanded={expanded}
              range={range}
              top={top}
              key={repoKey}
              repoKey={repoKey}
              isDuplicateRepoName={!!(name && duplicateRepoNames.has(name))}
              jobs={buckets[repoKey]}
              onToggle={onToggle}
              onToggleAll={onToggleAll}
              width={width}
            />
          );
        })
      ) : (
        <RunsEmptyOrLoading loading={loading} includesTicks={includesTicks} />
      )}
    </Timeline>
  );
};

interface TimelineSectionProps {
  expanded: boolean;
  repoKey: string;
  isDuplicateRepoName: boolean;
  jobs: TimelineJob[];
  top: number;
  range: [number, number];
  width: number;
  onToggle: (repoAddress: RepoAddress) => void;
  onToggleAll: (expanded: boolean) => void;
}

const TimelineSection = (props: TimelineSectionProps) => {
  const {
    expanded,
    onToggle,
    onToggleAll,
    repoKey,
    isDuplicateRepoName,
    jobs,
    range,
    top,
    width,
  } = props;
  const repoAddress = repoAddressFromPath(repoKey);
  const repoName = repoAddress?.name || 'Unknown repo';
  const repoLocation = repoAddress?.location || 'Unknown location';

  const onClick = React.useCallback(
    (e: React.MouseEvent) => {
      if (e.getModifierState('Shift')) {
        onToggleAll(!expanded);
      } else {
        repoAddress && onToggle(repoAddress);
      }
    },
    [expanded, onToggle, onToggleAll, repoAddress],
  );

  return (
    <div>
      <SectionHeaderContainer $top={top}>
        <RepoSectionHeader
          expanded={expanded}
          repoName={repoName}
          repoLocation={repoLocation}
          onClick={onClick}
          showLocation={isDuplicateRepoName}
          rightElement={<RunStatusTags jobs={jobs} />}
        />
      </SectionHeaderContainer>
      {expanded
        ? jobs.map((job, ii) => (
            <RunTimelineRow
              key={job.key}
              job={job}
              top={top + SECTION_HEADER_HEIGHT + ii * ROW_HEIGHT}
              range={range}
              width={width}
            />
          ))
        : null}
    </div>
  );
};

const RunStatusTags = React.memo(({jobs}: {jobs: TimelineJob[]}) => {
  const {inProgressCount, failedCount, succeededCount} = React.useMemo(() => {
    let inProgressCount = 0;
    let failedCount = 0;
    let succeededCount = 0;
    jobs.forEach(({runs}) => {
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
  }, [jobs]);

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
});

const StatusSpan = styled.span`
  white-space: nowrap;
`;

const SectionHeaderContainer = styled.div<{$top: number}>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;

  ${({$top}) => `transform: translateY(${$top}px);`}
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
  range: [number, number];
}

const dateTimeOptions: Intl.DateTimeFormatOptions = {
  month: 'numeric',
  day: 'numeric',
  year: 'numeric',
};

const dateTimeOptionsWithTimezone: Intl.DateTimeFormatOptions = {
  month: 'numeric',
  day: 'numeric',
  year: 'numeric',
  timeZoneName: 'short',
};

const timeOnlyOptions: Intl.DateTimeFormatOptions = {
  hour: 'numeric',
};

const TimeDividers = (props: TimeDividersProps) => {
  const {interval, range, height} = props;
  const [start, end] = range;
  const formatDateTime = useFormatDateTime();

  const dateMarkers: DateMarker[] = React.useMemo(() => {
    const totalTime = end - start;
    const startDate = new Date(start);
    const startDateStringWithTimezone = formatDateTime(startDate, dateTimeOptionsWithTimezone);

    const dayBoundaries = [];

    // Create a date at midnight on this date in this timezone.
    let cursor = new Date(startDateStringWithTimezone);

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
  }, [end, formatDateTime, start]);

  const timeMarkers: TimeMarker[] = React.useMemo(() => {
    const totalTime = end - start;
    const startGap = start % interval;
    const firstMarker = start - startGap;
    const markerCount = Math.ceil(totalTime / interval) + 1;
    return [...new Array(markerCount)]
      .map((_, ii) => {
        const time = firstMarker + ii * interval;
        const date = new Date(time);
        const label = formatDateTime(date, timeOnlyOptions).replace(' ', '');
        return {
          label,
          key: date.toString(),
          left: ((time - start) / totalTime) * 100,
        };
      })
      .filter((marker) => marker.left > 0);
  }, [end, start, interval, formatDateTime]);

  const now = Date.now();
  const nowLeft = `${(((now - start) / (end - start)) * 100).toPrecision(3)}%`;

  return (
    <DividerContainer style={{height: `${height}px`}}>
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
        <DividerLine style={{left: 0, backgroundColor: Colors.Gray200}} />
        {timeMarkers.map((marker) => (
          <DividerLine key={marker.key} style={{left: `${marker.left.toPrecision(3)}%`}} />
        ))}
        {now >= start && now <= end ? (
          <>
            <NowMarker style={{left: nowLeft}}>Now</NowMarker>
            <DividerLine style={{left: nowLeft, backgroundColor: Colors.Blue500, zIndex: 1}} />
          </>
        ) : null}
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
  color: ${Colors.Gray800};
`;

const DividerLabels = styled.div`
  display: flex;
  align-items: center;
  box-shadow: inset 1px 0 0 ${Colors.KeylineGray}, inset 0 1px 0 ${Colors.KeylineGray},
    inset -1px 0 0 ${Colors.KeylineGray};
  height: ${TIME_HEADER_HEIGHT}px;
  position: relative;
  user-select: none;
  font-size: 12px;
  width: 100%;
  overflow: hidden;
`;

const DateLabel = styled.div`
  position: absolute;
  padding: 8px 0;
  box-shadow: inset 1px 0 0 ${Colors.KeylineGray};
  white-space: nowrap;
`;

const TimeLabel = styled.div`
  position: absolute;
  padding: 8px;
  box-shadow: inset 1px 0 0 ${Colors.KeylineGray};
  white-space: nowrap;
`;

const DividerLines = styled.div`
  height: 100%;
  position: relative;
  width: 100%;
  box-shadow: inset 1px 0 0 ${Colors.KeylineGray}, inset -1px 0 0 ${Colors.KeylineGray};
`;

const DividerLine = styled.div`
  background-color: ${Colors.KeylineGray};
  height: 100%;
  position: absolute;
  top: 0;
  width: 1px;
`;

const NowMarker = styled.div`
  background-color: ${Colors.Blue500};
  border-radius: 1px;
  color: ${Colors.White};
  cursor: default;
  font-size: 12px;
  line-height: 12px;
  margin-left: -12px;
  padding: 1px 4px;
  position: absolute;
  top: -14px;
  user-select: none;
`;

const MIN_CHUNK_WIDTH = 2;
const MIN_WIDTH_FOR_MULTIPLE = 12;

const RunTimelineRow = ({
  job,
  top,
  range,
  width: containerWidth,
}: {
  job: TimelineJob;
  top: number;
  range: [number, number];
  width: number;
}) => {
  const [start, end] = range;
  const width = containerWidth - LEFT_SIDE_SPACE_ALLOTTED;
  const {runs} = job;

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

  if (!job.runs.length) {
    return null;
  }

  return (
    <Row $top={top}>
      <JobName>
        <Icon name={job.jobType === 'asset' ? 'asset' : 'job'} />
        <div style={{width: LABEL_WIDTH}}>
          {job.jobType === 'asset' ? (
            <span style={{color: Colors.Gray900}}>
              <MiddleTruncate text={job.jobName} />
            </span>
          ) : (
            <Link to={job.path}>
              <MiddleTruncate text={job.jobName} />
            </Link>
          )}
        </div>
      </JobName>
      <RunChunks>
        {batched.map((batch) => {
          const {left, width, runs} = batch;
          const runCount = runs.length;
          return (
            <RunChunk
              key={batch.runs[0].id}
              $background={mergeStatusToBackground(batch.runs)}
              $multiple={runCount > 1}
              style={{
                left: `${left}px`,
                width: `${width}px`,
              }}
            >
              <Popover
                content={<RunHoverContent job={job} batch={batch} />}
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
    </Row>
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
      background={Colors.White}
      padding={{vertical: 24}}
      flex={{direction: 'row', justifyContent: 'center'}}
      border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
    >
      {content()}
    </Box>
  );
};

const Timeline = styled.div<{$height: number}>`
  ${({$height}) => `height: ${$height}px;`}
  position: relative;
`;

const Row = styled.div<{$top: number}>`
  align-items: center;
  box-shadow: inset 0 -1px 0 ${Colors.KeylineGray};
  display: flex;
  flex-direction: row;
  width: 100%;
  height: ${ROW_HEIGHT + 1}px;
  padding: 1px 0;
  position: absolute;
  left: 0;
  top: 0;

  ${({$top}) => `transform: translateY(${$top}px);`}

  :first-child, :hover {
    box-shadow: inset 0 1px 0 ${Colors.KeylineGray}, inset 0 -1px 0 ${Colors.KeylineGray};
  }

  :hover {
    background-color: ${Colors.Gray10};
  }
`;

const JobName = styled.div`
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

const RunChunks = styled.div`
  flex: 1;
  position: relative;
  height: ${ROW_HEIGHT}px;
`;

interface ChunkProps {
  $background: string;
  $multiple: boolean;
}

const RunChunk = styled.div<ChunkProps>`
  align-items: center;
  background: ${({$background}) => $background};
  border-radius: 2px;
  height: ${ROW_HEIGHT - 4}px;
  position: absolute;
  top: 2px;
  ${({$multiple}) => ($multiple ? `min-width: ${MIN_WIDTH_FOR_MULTIPLE}px` : null)};

  transition: background-color 300ms linear, width 300ms ease-in-out;

  .chunk-popover-target {
    display: block;
    height: 100%;
    width: 100%;
  }
`;

const BatchCount = styled.div`
  color: ${Colors.White};
  cursor: default;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 600;
  user-select: none;
`;

interface RunHoverContentProps {
  job: TimelineJob;
  batch: RunBatch<TimelineRun>;
}

const RunHoverContent = (props: RunHoverContentProps) => {
  const {job, batch} = props;
  const sliced = batch.runs.slice(0, 50);
  const remaining = batch.runs.length - sliced.length;

  return (
    <Box style={{width: '260px'}}>
      <Box padding={12} border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <HoverContentJobName>{job.jobName}</HoverContentJobName>
      </Box>
      <div style={{maxHeight: '240px', overflowY: 'auto'}}>
        {sliced.map((run, ii) => (
          <Box
            key={run.id}
            border={ii > 0 ? {side: 'top', width: 1, color: Colors.KeylineGray} : null}
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
                <TimeElapsed startUnix={run.startTime / 1000} endUnix={run.endTime / 1000} />
              )}
            </Mono>
          </Box>
        ))}
      </div>
      {remaining > 0 ? (
        <Box padding={12} border={{side: 'top', width: 1, color: Colors.KeylineGray}}>
          <Link to={`${job.path}runs`}>+ {remaining} more</Link>
        </Box>
      ) : null}
    </Box>
  );
};

const HoverContentJobName = styled.strong`
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
`;
