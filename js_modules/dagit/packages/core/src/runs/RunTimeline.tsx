import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Popover, Mono, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationStatus, RunStatus} from '../types/globalTypes';
import {LoadingSpinner} from '../ui/Loading';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {RunStatusDot} from './RunStatusDots';
import {
  doneStatuses,
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from './RunStatuses';
import {TimeElapsed} from './TimeElapsed';
import {batchRunsForTimeline, overlap, RunBatch} from './batchRunsForTimeline';
import {RunTimelineQuery, RunTimelineQueryVariables} from './types/RunTimelineQuery';

const ROW_HEIGHT = 24;
const TIME_HEADER_HEIGHT = 36;
const LABEL_WIDTH = 232;

const ONE_HOUR_MSEC = 60 * 60 * 1000;

export type TimelineRun = {
  id: string;
  status: RunStatus | 'SCHEDULED';
  startTime: number;
  endTime: number;
};

export type TimelineJob = {
  key: string;
  jobName: string;
  path: string;
  runs: TimelineRun[];
};

export type HourWindow = '1' | '6' | '12' | '24';

export const makeJobKey = (repoAddress: RepoAddress, jobName: string) => {
  return `${jobName}-${repoAddressAsString(repoAddress)}`;
};

export const RunTimelineContainer = ({
  range,
  jobs,
  hourWindow,
}: {
  range: [number, number];
  jobs: TimelineJob[];
  hourWindow: HourWindow;
}) => {
  const [start, end] = range;
  const [jobsWithRuns, setJobsWithRuns] = React.useState<TimelineJob[]>([]);
  const [loadedWindow, setLoadedWindow] = React.useState<HourWindow>();

  const {data, loading} = useQuery<RunTimelineQuery, RunTimelineQueryVariables>(
    RUN_TIMELINE_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
      variables: {
        inProgressFilter: {
          statuses: [RunStatus.CANCELING, RunStatus.STARTED],
          createdBefore: end / 1000.0,
        },
        terminatedFilter: {
          statuses: Array.from(doneStatuses),
          createdBefore: end / 1000.0,
          updatedAfter: start / 1000.0,
        },
      },
    },
  );
  const jobsByKey = React.useMemo(() => {
    return jobs.reduce((accum, job: TimelineJob) => {
      return {...accum, [job.key]: job};
    }, {} as {[key: string]: TimelineJob});
  }, [jobs]);

  React.useEffect(() => {
    if (loading) {
      return;
    }
    const {unterminated, terminated, workspaceOrError} = data || {};

    const runsByJob: {[jobName: string]: TimelineRun[]} = {};
    const now = Date.now();

    // fetch all the runs in the given range
    [
      ...(unterminated?.__typename === 'Runs' ? unterminated.results : []),
      ...(terminated?.__typename === 'Runs' ? terminated.results : []),
    ].forEach((run) => {
      if (!run.startTime) {
        return;
      }
      if (
        !overlap(
          {start, end},
          {
            start: run.startTime * 1000,
            end: run.endTime ? run.endTime * 1000 : now,
          },
        )
      ) {
        return;
      }
      runsByJob[run.pipelineName] = [
        ...(runsByJob[run.pipelineName] || []),
        {
          id: run.id,
          status: run.status,
          startTime: run.startTime * 1000,
          endTime: run.endTime ? run.endTime * 1000 : now,
        },
      ];
    });

    const jobs = [];
    if (workspaceOrError && workspaceOrError.__typename === 'Workspace') {
      for (const locationEntry of workspaceOrError.locationEntries) {
        if (
          locationEntry.__typename === 'WorkspaceLocationEntry' &&
          locationEntry.locationOrLoadError?.__typename === 'RepositoryLocation'
        ) {
          for (const repository of locationEntry.locationOrLoadError.repositories) {
            const repoAddress = buildRepoAddress(
              repository.name,
              locationEntry.locationOrLoadError.name,
            );
            for (const pipeline of repository.pipelines) {
              const jobKey = makeJobKey(repoAddress, pipeline.name);
              if (!(jobKey in jobsByKey)) {
                continue;
              }

              const schedules = (repository.schedules || []).filter(
                (schedule) => schedule.pipelineName === pipeline.name,
              );

              const jobTicks: TimelineRun[] = [];
              for (const schedule of schedules) {
                if (schedule.scheduleState.status === InstigationStatus.RUNNING) {
                  schedule.futureTicks.results.forEach(({timestamp}) => {
                    const startTime = timestamp * 1000;
                    if (overlap({start, end}, {start: startTime, end: startTime})) {
                      jobTicks.push({
                        id: `${schedule.pipelineName}-future-run-${timestamp}`,
                        status: 'SCHEDULED',
                        startTime,
                        endTime: startTime + 10 * 1000,
                      });
                    }
                  });
                }
              }

              const jobRuns = runsByJob[pipeline.name] || [];
              if (jobTicks.length || jobRuns.length) {
                jobs.push({
                  key: jobKey,
                  jobName: pipeline.name,
                  path: workspacePipelinePath({
                    repoName: repoAddress.name,
                    repoLocation: repoAddress.location,
                    pipelineName: pipeline.name,
                    isJob: pipeline.isJob,
                  }),
                  runs: [...jobRuns, ...jobTicks],
                });
              }
            }
          }
        }
      }
    }

    const earliest = jobs.reduce((accum, job) => {
      const startTimes = job.runs.map((job) => job.startTime);
      return {...accum, [job.key]: Math.min(...startTimes)};
    }, {} as {[jobKey: string]: number});

    setJobsWithRuns(jobs.sort((a, b) => earliest[a.key] - earliest[b.key]));
    setLoadedWindow(hourWindow);
  }, [data, start, end, loading, jobsByKey, hourWindow]);

  if (loading && hourWindow !== loadedWindow) {
    return <LoadingSpinner purpose="section" />;
  }
  return <RunTimeline range={[start, end]} jobs={jobsWithRuns} />;
};

export const RunTimeline = ({jobs, range}: {jobs: TimelineJob[]; range: [number, number]}) => {
  const [width, setWidth] = React.useState<number | null>(null);
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

  const height = ROW_HEIGHT * (jobs.length || 1);

  return (
    <Timeline $height={TIME_HEADER_HEIGHT + height} ref={containerRef}>
      {width ? (
        jobs.length ? (
          <>
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
          </>
        ) : (
          <NoRunsTimeline />
        )
      ) : null}
    </Timeline>
  );
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
                content={<RunHoverContent jobKey={job.key} batch={batch} />}
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
  font-family: ${FontFamily.monospace};
  font-size: 14px;
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
  font-size: 12px;
  user-select: none;
`;

interface RunHoverContentProps {
  jobKey: string;
  batch: RunBatch<TimelineRun>;
}

const RunHoverContent = (props: RunHoverContentProps) => {
  const {jobKey, batch} = props;
  return (
    <Box style={{width: '260px'}}>
      <Box padding={12} border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <HoverContentJobName>{jobKey}</HoverContentJobName>
      </Box>
      <div style={{maxHeight: '240px', overflowY: 'auto'}}>
        {batch.runs.map((run, ii) => (
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

const RUN_TIMELINE_QUERY = gql`
  query RunTimelineQuery($inProgressFilter: RunsFilter!, $terminatedFilter: RunsFilter!) {
    unterminated: runsOrError(filter: $inProgressFilter) {
      ... on Runs {
        results {
          id
          pipelineName
          ...RunTimeFragment
        }
      }
    }
    terminated: runsOrError(filter: $terminatedFilter) {
      ... on Runs {
        results {
          id
          pipelineName
          ...RunTimeFragment
        }
      }
    }
    workspaceOrError {
      ... on Workspace {
        locationEntries {
          id
          name
          loadStatus
          displayMetadata {
            key
            value
          }
          locationOrLoadError {
            ... on RepositoryLocation {
              id
              name
              repositories {
                id
                name
                pipelines {
                  id
                  name
                  isJob
                }
                schedules {
                  id
                  name
                  pipelineName
                  scheduleState {
                    id
                    status
                  }
                  ...ScheduleFutureTicksFragment
                }
              }
            }
          }
        }
      }
    }
  }
  ${RUN_TIME_FRAGMENT}
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
`;
