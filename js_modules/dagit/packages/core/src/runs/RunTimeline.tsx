import {Box, Colors, Popover, Mono, FontFamily, Tooltip, Tag} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {RunStatus} from '../types/globalTypes';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';
import {RepoAddress} from '../workspace/types';

import {RepoSectionHeader, SECTION_HEADER_HEIGHT} from './RepoSectionHeader';
import {RunStatusDot} from './RunStatusDots';
import {failedStatuses, inProgressStatuses, queuedStatuses, successStatuses} from './RunStatuses';
import {TimeElapsed} from './TimeElapsed';
import {batchRunsForTimeline, RunBatch} from './batchRunsForTimeline';

const ROW_HEIGHT = 32;
const TIME_HEADER_HEIGHT = 36;
const EMPTY_STATE_HEIGHT = 48;
const LABEL_WIDTH = 320;

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
  path: string;
  runs: TimelineRun[];
};

interface Props {
  bucketByRepo?: boolean;
  jobs: TimelineJob[];
  range: [number, number];
}

const EXPANSION_STATE_STORAGE_KEY = 'timeline-expansion-state';

export const RunTimeline = (props: Props) => {
  const {bucketByRepo = false, jobs, range} = props;
  const [width, setWidth] = React.useState<number | null>(null);
  const {expandedKeys, onToggle} = useRepoExpansionState(EXPANSION_STATE_STORAGE_KEY);

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

  if (!width || !jobs.length) {
    return (
      <Timeline $height={TIME_HEADER_HEIGHT + EMPTY_STATE_HEIGHT} ref={containerRef}>
        {width ? <NoRunsTimeline /> : null}
      </Timeline>
    );
  }

  if (!bucketByRepo) {
    const height = ROW_HEIGHT * (jobs.length || 1);
    return (
      <Timeline $height={TIME_HEADER_HEIGHT + height} ref={containerRef}>
        <TimeDividers interval={ONE_HOUR_MSEC} range={range} height={height} />
        <div>
          {jobs.map((job, ii) => (
            <RunTimelineRow
              key={job.key}
              job={job}
              top={ii * ROW_HEIGHT + TIME_HEADER_HEIGHT}
              range={range}
              width={width}
            />
          ))}
        </div>
      </Timeline>
    );
  }

  const buckets = jobs.reduce((accum, job) => {
    const {repoAddress} = job;
    const repoKey = repoAddressAsString(repoAddress);
    const jobsForRepo = accum[repoKey] || [];
    return {...accum, [repoKey]: [...jobsForRepo, job]};
  }, {});

  const repoOrder = Object.keys(buckets).sort((a, b) =>
    a.toLocaleLowerCase().localeCompare(b.toLocaleLowerCase()),
  );

  let nextTop = TIME_HEADER_HEIGHT;
  const expandedRepos = repoOrder.filter((repoKey) => expandedKeys.includes(repoKey));
  const expandedJobCount = expandedRepos.reduce(
    (accum, repoKey) => accum + buckets[repoKey].length,
    0,
  );
  const height = repoOrder.length * SECTION_HEADER_HEIGHT + ROW_HEIGHT * expandedJobCount;
  const duplicateRepoNames = findDuplicateRepoNames(
    repoOrder.map((repoKey) => repoAddressFromPath(repoKey)?.name || ''),
  );

  return (
    <Timeline $height={TIME_HEADER_HEIGHT + height} ref={containerRef}>
      <TimeDividers interval={ONE_HOUR_MSEC} range={range} height={height} />
      {repoOrder.map((repoKey) => {
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
            width={width}
          />
        );
      })}
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
}

const TimelineSection = (props: TimelineSectionProps) => {
  const {expanded, onToggle, repoKey, isDuplicateRepoName, jobs, range, top, width} = props;
  const repoAddress = repoAddressFromPath(repoKey);
  const repoName = repoAddress?.name || 'Unknown repo';
  const repoLocation = repoAddress?.location || 'Unknown location';
  const onClick = React.useCallback(() => {
    repoAddress && onToggle(repoAddress);
  }, [onToggle, repoAddress]);
  const jobCount = jobs.length;

  return (
    <div>
      <SectionHeaderContainer $top={top}>
        <RepoSectionHeader
          expanded={expanded}
          repoName={repoName}
          repoLocation={repoLocation}
          onClick={onClick}
          showLocation={isDuplicateRepoName}
          rightElement={
            <Tooltip
              content={
                <span style={{whiteSpace: 'nowrap'}}>
                  {jobCount === 1 ? '1 job with runs' : `${jobCount} jobs with runs`}
                </span>
              }
              placement="top"
            >
              <Tag intent="primary">{jobCount}</Tag>
            </Tooltip>
          }
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

const SectionHeaderContainer = styled.div<{$top: number}>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;

  ${({$top}) => `transform: translateY(${$top}px);`}
`;

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

const TimeDividers = (props: TimeDividersProps) => {
  const {interval, range, height} = props;
  const [start, end] = range;
  const locale = navigator.language;
  const [timezone] = React.useContext(TimezoneContext);

  const timeMarkers: TimeMarker[] = React.useMemo(() => {
    const totalTime = end - start;
    const startGap = start % interval;
    const firstMarker = start - startGap;
    const markerCount = Math.ceil(totalTime / interval) + 1;
    return [...new Array(markerCount)]
      .map((_, ii) => {
        const time = firstMarker + ii * interval;
        const date = new Date(time);
        const label = date.toLocaleString(locale, {
          hour: '2-digit',
          timeZone: timezone === 'Automatic' ? browserTimezone() : timezone,
        });
        return {
          label,
          key: date.toString(),
          left: ((time - start) / totalTime) * 100,
        };
      })
      .filter((marker) => marker.left > 0);
  }, [end, start, interval, locale, timezone]);

  const now = Date.now();
  const nowLeft = `${(((now - start) / (end - start)) * 100).toPrecision(3)}%`;

  return (
    <DividerContainer style={{height: `${height}px`}}>
      <DividerLabels>
        {timeMarkers.map((marker) => (
          <DividerLabel key={marker.key} style={{left: `${marker.left.toPrecision(3)}%`}}>
            {marker.label}
          </DividerLabel>
        ))}
      </DividerLabels>
      <DividerLines>
        <DividerLine style={{left: 0, backgroundColor: Colors.Gray200}} />
        {timeMarkers.map((marker) => (
          <DividerLine key={marker.key} style={{left: `${marker.left.toPrecision(3)}%`}} />
        ))}
        {now >= start && now <= end ? (
          <DividerLine style={{left: nowLeft, backgroundColor: Colors.Blue500, zIndex: 1}} />
        ) : null}
      </DividerLines>
    </DividerContainer>
  );
};

const DividerContainer = styled.div`
  position: absolute;
  top: 0;
  left: ${LABEL_WIDTH}px;
  right: 0;
  font-family: ${FontFamily.monospace};
  color: ${Colors.Gray400};
`;

const DividerLabels = styled.div`
  display: flex;
  align-items: center;
  height: ${TIME_HEADER_HEIGHT}px;
  position: relative;
  user-select: none;
  width: 100%;
`;

const DividerLabel = styled.div`
  position: absolute;
  transform: translateX(-50%);
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

const mergeStatusToColor = (runs: TimelineRun[]) => {
  let anyInProgress = false;
  let anyQueued = false;
  let anyFailed = false;
  let anySucceeded = false;
  let anyScheduled = false;

  runs.forEach(({status}) => {
    if (status === 'SCHEDULED') {
      anyScheduled = true;
    } else if (queuedStatuses.has(status)) {
      anyQueued = true;
    } else if (inProgressStatuses.has(status)) {
      anyInProgress = true;
    } else if (failedStatuses.has(status)) {
      anyFailed = true;
    } else if (successStatuses.has(status)) {
      anySucceeded = true;
    }
  });

  if (anyQueued) {
    return Colors.Blue200;
  }
  if (anyInProgress) {
    return Colors.Blue500;
  }
  if (anyFailed) {
    return Colors.Red500;
  }
  if (anySucceeded) {
    return Colors.Green500;
  }
  if (anyScheduled) {
    return Colors.Blue200;
  }

  return Colors.Gray500;
};

const MIN_CHUNK_WIDTH = 2;
const MIN_WIDTH_FOR_MULTIPLE = 16;

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
  // const {jobKey, jobLabel, jobPath, runs, top, range, width: containerWidth} = props;
  const [start, end] = range;
  const width = containerWidth - LABEL_WIDTH;
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
        <Link to={job.path}>{job.jobName}</Link>
      </JobName>
      <RunChunks>
        {batched.map((batch) => {
          const {left, width, runs} = batch;
          const runCount = runs.length;
          return (
            <RunChunk
              key={batch.runs[0].id}
              $color={mergeStatusToColor(batch.runs)}
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

const NoRunsTimeline = () => (
  <Box flex={{justifyContent: 'center', alignItems: 'center'}} padding={24}>
    No runs or upcoming runs found for this time window.
  </Box>
);

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
  justify-content: space-between;
  line-height: 16px;
  overflow: hidden;
  padding: 0 12px 0 24px;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: ${LABEL_WIDTH}px;
`;

const RunChunks = styled.div`
  flex: 1;
  position: relative;
  height: ${ROW_HEIGHT}px;
`;

interface ChunkProps {
  $color: string;
  $multiple: boolean;
}

const RunChunk = styled.div<ChunkProps>`
  align-items: center;
  background-color: ${({$color}) => $color};
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
  font-size: 12px;
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
                <Link to={`/instance/runs/${run.id}`}>
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
