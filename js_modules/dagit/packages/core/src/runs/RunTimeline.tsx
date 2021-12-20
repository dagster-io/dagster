import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {RunStatus} from '../types/globalTypes';
import {ColorsWIP} from '../ui/Colors';
import {FontFamily} from '../ui/styles';

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
  jobs: {[jobKey: string]: RunForJob[]};
  range: [number, number];
}

export const RunTimeline = (props: Props) => {
  const {jobs, range} = props;

  const jobList = React.useMemo(() => {
    const jobKeys = Object.keys(jobs);
    const earliest = jobKeys.reduce((accum, jobKey) => {
      const startTimes = jobs[jobKey].map((job) => job.startTime || 0);
      return {...accum, [jobKey]: Math.min(...startTimes)};
    }, {} as {[jobName: string]: number});

    return jobKeys
      .sort((a, b) => earliest[a] - earliest[b])
      .map((jobKey) => ({jobKey, runs: jobs[jobKey]}));
  }, [jobs]);

  const height = ROW_HEIGHT * jobList.length;

  return (
    <Timeline $height={height}>
      <TimeDividers interval={ONE_HOUR_MSEC} range={range} height={height} />
      <div>
        {jobList.map(({jobKey, runs}, ii) => (
          <RunTimelineRow
            key={jobKey}
            jobKey={jobKey}
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
    const markerCount = Math.floor(totalTime / interval);
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
) => {
  return !(a.endTime <= b.startTime || b.endTime <= a.startTime);
};

type RunBatch = {
  runs: RunForJob[];
  startTime: number;
  endTime: number;
};

interface RowProps {
  jobKey: string;
  runs: RunForJob[];
  top: number;
  range: [number, number];
}

const RunTimelineRow = (props: RowProps) => {
  const {jobKey, runs, top, range} = props;
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
        <Link to={`/${jobKey}`}>{jobKey}</Link>
      </JobName>
      <RunChunks>
        {batched.map((batch) => {
          return (
            <RunChunk
              key={batch.runs[0].id}
              $status={batch.runs[0].status}
              $left={(batch.startTime - start) / rangeLength}
              $width={(batch.endTime - batch.startTime) / rangeLength}
            >
              {batch.runs.length > 1 ? <BatchCount>{batch.runs.length}</BatchCount> : null}
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
  text-overflow: ellpisis;
  white-space: nowrap;
  width: ${LABEL_WIDTH}px;
`;

const RunChunks = styled.div`
  flex: 1;
  position: relative;
  height: ${ROW_HEIGHT}px;
`;

interface ChunkProps {
  $status: RunStatus;
  $left: number;
  $width: number;
}

const backgroundColor = ({$status}: ChunkProps) => {
  switch ($status) {
    case RunStatus.SUCCESS:
      return ColorsWIP.Green500;
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
    case RunStatus.FAILURE:
      return ColorsWIP.Red500;
    default:
      return ColorsWIP.Blue500;
  }
};

const RunChunk = styled.div.attrs((props: ChunkProps) => ({
  style: {
    left: `${(props.$left * 100).toPrecision(5)}%`,
    width: `${(props.$width * 100).toPrecision(5)}%`,
  },
}))`
  align-items: center;
  background-color: ${backgroundColor};
  border-radius: 2px;
  display: flex;
  flex-direction: row;
  justify-content: center;
  height: ${ROW_HEIGHT - 4}px;
  position: absolute;
  top: 2px;
`;

const BatchCount = styled.div`
  color: ${ColorsWIP.White};
  cursor: default;
  font-size: 12px;
  user-select: none;
`;
