import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {InstigationStatus, RunStatus} from '../types/globalTypes';
import {LoadingSpinner} from '../ui/Loading';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {doneStatuses} from './RunStatuses';
import {RunTimeline, TimelineJob, TimelineRun} from './RunTimeline';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {overlap} from './batchRunsForTimeline';
import {RunTimelineQuery, RunTimelineQueryVariables} from './types/RunTimelineQuery';

export type HourWindow = '1' | '6' | '12' | '24';

export const makeJobKey = (repoAddress: RepoAddress, jobName: string) =>
  `${jobName}-${repoAddressAsString(repoAddress)}`;

export const QueryfulRunTimeline = ({
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

  const {flagRunBucketing} = useFeatureFlags();

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
                  repoAddress,
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

  return <RunTimeline range={[start, end]} jobs={jobsWithRuns} bucketByRepo={flagRunBucketing} />;
};

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
