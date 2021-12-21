import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {RunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Popover} from '../ui/Popover';
import {Mono} from '../ui/Text';
import {FontFamily} from '../ui/styles';

import {RunStatusDot} from './RunStatusDots';
import {failedStatuses, inProgressStatuses, queuedStatuses, successStatuses} from './RunStatuses';
import {TimeElapsed} from './TimeElapsed';

const ROW_HEIGHT = 24;
const TIME_HEADER_HEIGHT = 36;
const LABEL_WIDTH = 232;

const ONE_HOUR_MSEC = 60 * 60 * 1000;

type RunForJob = {
  id: string;
  status: RunStatus;
  startTime: number;
  endTime: number;
};

interface Props {
  jobs: {
    [jobKey: string]: {
      path: string;
      runs: RunForJob[];
    };
  };
  range: [number, number];
}

export const RunTimeline = (props: Props) => {
  const {jobs, range} = props;

  const jobList = React.useMemo(() => {
    const jobKeys = Object.keys(jobs);
    const earliest = jobKeys.reduce((accum, jobKey) => {
      const startTimes = jobs[jobKey].runs.map((job) => job.startTime || 0);
      return {...accum, [jobKey]: Math.min(...startTimes)};
    }, {} as {[jobName: string]: number});

    return jobKeys
      .sort((a, b) => earliest[a] - earliest[b])
      .map((jobKey) => ({jobKey, ...jobs[jobKey]}));
  }, [jobs]);

  const height = ROW_HEIGHT * jobList.length;

  return (
    <Timeline $height={height}>
      <TimeDividers interval={ONE_HOUR_MSEC} range={range} height={height} />
      <div>
        {jobList.map(({jobKey, path, runs}, ii) => (
          <RunTimelineRow
            key={jobKey}
            jobKey={jobKey}
            jobPath={path}
            runs={runs}
            top={ii * ROW_HEIGHT + TIME_HEADER_HEIGHT}
            range={range}
          />
        ))}
      </div>
    </Timeline>
  );
};

type TimeMarker = {
  label: string;
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
        return {
          label: date.toLocaleString(locale, {
            hour: '2-digit',
            timeZone: timezone === 'Automatic' ? browserTimezone() : timezone,
          }),
          left: ((time - start) / totalTime) * 100,
        };
      })
      .filter((marker) => marker.left > 0);
  }, [end, start, interval, locale, timezone]);

  return (
    <DividerContainer style={{height: `${height}px`}}>
      <DividerLabels>
        {timeMarkers.map((marker) => (
          <DividerLabel key={marker.label} style={{left: `${marker.left.toPrecision(3)}%`}}>
            {marker.label}
          </DividerLabel>
        ))}
      </DividerLabels>
      <DividerLines>
        {timeMarkers.map((marker) => (
          <DividerLine key={marker.label} style={{left: `${marker.left.toPrecision(3)}%`}} />
        ))}
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
  color: ${ColorsWIP.Gray400};
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
`;

const DividerLines = styled.div`
  height: 100%;
  position: relative;
  width: 100%;
  box-shadow: inset 1px 0 0 ${ColorsWIP.KeylineGray}, inset -1px 0 0 ${ColorsWIP.KeylineGray};
`;

const DividerLine = styled.div`
  background-color: ${ColorsWIP.KeylineGray};
  height: 100%;
  position: absolute;
  top: 0;
  width: 1px;
`;

const overlap = (
  a: {startTime: number; endTime: number},
  b: {startTime: number; endTime: number},
) => !(a.endTime <= b.startTime || b.endTime <= a.startTime);

type RunBatch = {
  runs: RunForJob[];
  startTime: number;
  endTime: number;
};

interface RowProps {
  jobKey: string;
  jobPath: string;
  runs: RunForJob[];
  top: number;
  range: [number, number];
}

const mergeStatusToColor = (runs: RunForJob[]) => {
  let anyInProgress = false;
  let anyQueued = false;
  let anyFailed = false;
  let anySucceeded = false;

  runs.forEach(({status}) => {
    if (queuedStatuses.has(status)) {
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
    return ColorsWIP.Blue200;
  }
  if (anyInProgress) {
    return ColorsWIP.Blue500;
  }
  if (anyFailed) {
    return ColorsWIP.Red500;
  }
  if (anySucceeded) {
    return ColorsWIP.Green500;
  }

  return ColorsWIP.Gray500;
};

const RunTimelineRow = (props: RowProps) => {
  const {jobKey, jobPath, runs, top, range} = props;
  const [start, end] = range;
  const rangeLength = end - start;

  // Batch overlapping runs in this row.
  const batched = React.useMemo(() => {
    const batches: RunBatch[] = runs
      .map((run) => ({
        runs: [run],
        startTime: run.startTime,
        endTime: run.endTime,
      }))
      .sort((a, b) => b.startTime - a.startTime);

    const consolidated = [];
    while (batches.length) {
      const current = batches.shift();
      const next = batches[0];
      if (current) {
        if (next && overlap(current, next)) {
          // Remove `next`, consolidate it with `current`, and unshift it back on.
          // This way, we keep looking for batches to consolidate with.
          batches.shift();
          current.runs = [...current.runs, ...next.runs];
          current.startTime = Math.min(current.startTime, next.startTime);
          current.endTime = Math.max(current.endTime, next.endTime);
          batches.unshift(current);
        } else {
          // If the next batch doesn't overlap, we've consolidated this batch
          // all we can. Move on!
          consolidated.push(current);
        }
      }
    }

    return consolidated;
  }, [runs]);

  return (
    <Row $top={top}>
      <JobName>
        <Link to={jobPath}>{jobKey}</Link>
      </JobName>
      <RunChunks>
        {batched.map((batch) => {
          const runCount = batch.runs.length;
          const left = (batch.startTime - start) / rangeLength;
          const width = (batch.endTime - batch.startTime) / rangeLength;
          return (
            <RunChunk
              key={batch.runs[0].id}
              $color={mergeStatusToColor(batch.runs)}
              $multiple={runCount > 1}
              style={{
                left: `${(left * 100).toPrecision(5)}%`,
                width: `${(width * 100).toPrecision(5)}%`,
              }}
            >
              <Popover
                content={<RunHoverContent jobKey={jobKey} batch={batch} />}
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

const Timeline = styled.div<{$height: number}>`
  ${({$height}) => `height: ${$height}px;`}
  position: relative;
`;

const Row = styled.div<{$top: number}>`
  align-items: center;
  box-shadow: inset 0 -1px 0 ${ColorsWIP.KeylineGray};
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
    box-shadow: inset 0 1px 0 ${ColorsWIP.KeylineGray}, inset 0 -1px 0 ${ColorsWIP.KeylineGray};
  }

  :hover {
    background-color: ${ColorsWIP.Gray10};
  }
`;

const JobName = styled.div`
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  line-height: 16px;
  overflow: hidden;
  padding: 0 12px 0 20px;
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
  ${({$multiple}) => ($multiple ? 'min-width: 16px' : null)};

  .chunk-popover-target {
    display: block;
    height: 100%;
    width: 100%;
  }
`;

const BatchCount = styled.div`
  color: ${ColorsWIP.White};
  cursor: default;
  font-size: 12px;
  user-select: none;
`;

interface RunHoverContentProps {
  jobKey: string;
  batch: RunBatch;
}

const RunHoverContent = (props: RunHoverContentProps) => {
  const {jobKey, batch} = props;
  return (
    <Box padding={4} style={{width: '220px'}}>
      <Box padding={8} border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}>
        <HoverContentJobName>{jobKey}</HoverContentJobName>
      </Box>
      {batch.runs.map((run, ii) => (
        <Box
          key={run.id}
          border={ii > 0 ? {side: 'top', width: 1, color: ColorsWIP.KeylineGray} : null}
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
          padding={8}
        >
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <RunStatusDot status={run.status} size={8} />
            <Link to={run.id}>
              <Mono>{run.id.slice(0, 8)}</Mono>
            </Link>
          </Box>
          <Mono>
            <TimeElapsed startUnix={run.startTime / 1000} endUnix={run.endTime / 1000} />
          </Mono>
        </Box>
      ))}
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
