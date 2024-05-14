import {gql, useQuery} from '@apollo/client';
import {useMemo} from 'react';

import {doneStatuses} from './RunStatuses';
import {TimelineJob, TimelineRun} from './RunTimeline';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {overlap} from './batchRunsForTimeline';
import {
  FutureTicksQuery,
  FutureTicksQueryVariables,
  TerimatedRunTimelineQuery,
  TerimatedRunTimelineQueryVariables,
  UnterminatedRunTimelineQuery,
  UnterminatedRunTimelineQueryVariables,
} from './types/useRunsForTimeline.types';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {InstigationStatus, RunStatus, RunsFilter} from '../graphql/types';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {useBlockTraceOnQueryResult} from '../performance/TraceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

export const useRunsForTimeline = (
  range: [number, number],
  runsFilter: RunsFilter = {},
  refreshInterval = FIFTEEN_SECONDS,
) => {
  const [start, end] = range;

  const startSec = start / 1000.0;
  const endSec = end / 1000.0;

  const unteriminatedRunsQueryData = useQuery<
    UnterminatedRunTimelineQuery,
    UnterminatedRunTimelineQueryVariables
  >(UNTERMINATED_RUN_TIMELINE_QUERY, {
    notifyOnNetworkStatusChange: true,
    // With a very large number of runs, operating on the Apollo cache is too expensive and
    // can block the main thread. This data has to be up-to-the-second fresh anyway, so just
    // skip the cache entirely.
    fetchPolicy: 'no-cache',
    variables: {
      inProgressFilter: {
        ...runsFilter,
        statuses: [RunStatus.CANCELING, RunStatus.STARTED],
        createdBefore: endSec,
      },
    },
  });

  const terminatedRunsQueryData = useQuery<
    TerimatedRunTimelineQuery,
    TerimatedRunTimelineQueryVariables
  >(TERMINATED_RUN_TIMELINE_QUERY, {
    notifyOnNetworkStatusChange: true,
    // With a very large number of runs, operating on the Apollo cache is too expensive and
    // can block the main thread. This data has to be up-to-the-second fresh anyway, so just
    // skip the cache entirely.
    fetchPolicy: 'no-cache',
    variables: {
      terminatedFilter: {
        ...runsFilter,
        statuses: Array.from(doneStatuses),
        createdBefore: endSec,
        updatedAfter: startSec,
      },
    },
  });

  const futureTicksQueryData = useQuery<FutureTicksQuery, FutureTicksQueryVariables>(
    FUTURE_TICKS_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      // With a very large number of runs, operating on the Apollo cache is too expensive and
      // can block the main thread. This data has to be up-to-the-second fresh anyway, so just
      // skip the cache entirely.
      fetchPolicy: 'no-cache',
      variables: {
        tickCursor: startSec,
        ticksUntil: endSec,
      },
    },
  );

  useBlockTraceOnQueryResult(unteriminatedRunsQueryData, 'UnterminatedRunTimelineQuery');
  useBlockTraceOnQueryResult(terminatedRunsQueryData, 'TerimatedRunTimelineQuery');
  useBlockTraceOnQueryResult(futureTicksQueryData, 'FutureTicksQuery');

  const {
    data: unterminatedRunsData,
    previousData: previousUnterminatedRunsData,
    loading: loadingUnterminatedRunsData,
    refetch: refetchUnterminatedRuns,
  } = unteriminatedRunsQueryData;
  const {
    data: terminatedRunsData,
    previousData: previousTerminatedRunsData,
    loading: loadingTerminatedRunsData,
    refetch: refetchTerminatedRuns,
  } = terminatedRunsQueryData;
  const {
    data: futureTicksData,
    previousData: previousFutureTicksData,
    loading: loadingFutureTicksData,
    refetch: refetchFutureTicks,
  } = futureTicksQueryData;

  const initialLoading =
    (loadingUnterminatedRunsData && !unterminatedRunsData) ||
    (loadingTerminatedRunsData && !terminatedRunsQueryData) ||
    (loadingFutureTicksData && !futureTicksData);

  const {unterminated} = unterminatedRunsData ||
    previousUnterminatedRunsData || {unterminated: undefined};
  const {terminated} = terminatedRunsData || previousTerminatedRunsData || {terminated: undefined};
  const {workspaceOrError} = futureTicksData ||
    previousFutureTicksData || {workspaceOrError: undefined};

  const runsByJobKey = useMemo(() => {
    const map: {[jobKey: string]: TimelineRun[]} = {};
    const now = Date.now();

    // fetch all the runs in the given range
    [
      ...(unterminated?.__typename === 'Runs' ? unterminated.results : []),
      ...(terminated?.__typename === 'Runs' ? terminated.results : []),
    ].forEach((run) => {
      if (!run.startTime) {
        return;
      }
      if (!run.repositoryOrigin) {
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

      const runJobKey = makeJobKey(
        {
          name: run.repositoryOrigin.repositoryName,
          location: run.repositoryOrigin.repositoryLocationName,
        },
        run.pipelineName,
      );

      map[runJobKey] = [
        ...(map[runJobKey] || []),
        {
          id: run.id,
          status: run.status,
          startTime: run.startTime * 1000,
          endTime: run.endTime ? run.endTime * 1000 : now,
        },
      ];
    });

    return map;
  }, [end, unterminated, terminated, start]);

  const jobsWithRuns: TimelineJob[] = useMemo(() => {
    if (!workspaceOrError || workspaceOrError.__typename !== 'Workspace') {
      return [];
    }

    const jobs: TimelineJob[] = [];
    for (const locationEntry of workspaceOrError.locationEntries) {
      if (
        locationEntry.__typename !== 'WorkspaceLocationEntry' ||
        locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation'
      ) {
        continue;
      }

      const now = Date.now();
      for (const repository of locationEntry.locationOrLoadError.repositories) {
        const repoAddress = buildRepoAddress(
          repository.name,
          locationEntry.locationOrLoadError.name,
        );

        for (const pipeline of repository.pipelines) {
          const schedules = (repository.schedules || []).filter(
            (schedule) => schedule.pipelineName === pipeline.name,
          );

          const jobTicks: TimelineRun[] = [];
          for (const schedule of schedules) {
            if (schedule.scheduleState.status === InstigationStatus.RUNNING) {
              schedule.futureTicks.results.forEach(({timestamp}) => {
                const startTime = timestamp! * 1000;
                if (startTime > now && overlap({start, end}, {start: startTime, end: startTime})) {
                  jobTicks.push({
                    id: `${schedule.pipelineName}-future-run-${timestamp}`,
                    status: 'SCHEDULED',
                    startTime,
                    endTime: startTime + 5 * 1000,
                  });
                }
              });
            }
          }

          const isAdHoc = isHiddenAssetGroupJob(pipeline.name);
          const jobKey = makeJobKey(repoAddress, pipeline.name);
          const jobName = isAdHoc ? 'Ad hoc materializations' : pipeline.name;

          const jobRuns = runsByJobKey[jobKey] || [];
          if (!jobTicks.length && !jobRuns.length) {
            continue;
          }

          const jobsAndTicksToAdd = [...jobRuns, ...jobTicks];
          if (isAdHoc) {
            const adHocJobs = jobs.find(
              (job) => job.jobType === 'asset' && job.repoAddress === repoAddress,
            );
            if (adHocJobs) {
              adHocJobs.runs.push(...jobsAndTicksToAdd);
              continue;
            }
          }

          jobs.push({
            key: jobKey,
            jobName,
            jobType: isAdHoc ? 'asset' : 'job',
            repoAddress,
            path: workspacePipelinePath({
              repoName: repoAddress.name,
              repoLocation: repoAddress.location,
              pipelineName: pipeline.name,
              isJob: pipeline.isJob,
            }),
            runs: [...jobRuns, ...jobTicks],
          } as TimelineJob);
        }
      }
    }

    const earliest = jobs.reduce(
      (accum, job) => {
        const startTimes = job.runs.map((job) => job.startTime);
        return {...accum, [job.key]: Math.min(...startTimes)};
      },
      {} as {[jobKey: string]: number},
    );

    return jobs.sort((a, b) => earliest[a.key]! - earliest[b.key]!);
  }, [workspaceOrError, runsByJobKey, start, end]);

  const refreshState = useRefreshAtInterval({
    refresh: async () => {
      await Promise.all([refetchFutureTicks(), refetchTerminatedRuns(), refetchUnterminatedRuns()]);
    },
    intervalMs: refreshInterval,
  });

  return useMemo(
    () => ({
      jobs: jobsWithRuns,
      initialLoading,
      refreshState,
    }),
    [initialLoading, jobsWithRuns, refreshState],
  );
};

export const makeJobKey = (repoAddress: RepoAddress, jobName: string) =>
  `${jobName}-${repoAddressAsHumanString(repoAddress)}`;

const UNTERMINATED_RUN_TIMELINE_QUERY = gql`
  query UnterminatedRunTimelineQuery($inProgressFilter: RunsFilter!, $limit: Int) {
    unterminated: runsOrError(filter: $inProgressFilter, limit: $limit) {
      ... on Runs {
        results {
          id
          pipelineName
          repositoryOrigin {
            id
            repositoryName
            repositoryLocationName
          }
          ...RunTimeFragment
        }
      }
    }
  }
`;

const TERMINATED_RUN_TIMELINE_QUERY = gql`
  query TerimatedRunTimelineQuery($terminatedFilter: RunsFilter!, $limit: Int) {
    terminated: runsOrError(filter: $terminatedFilter, limit: $limit) {
      ... on Runs {
        results {
          id
          pipelineName
          repositoryOrigin {
            id
            repositoryName
            repositoryLocationName
          }
          ...RunTimeFragment
        }
      }
    }
  }

  ${RUN_TIME_FRAGMENT}
`;

const FUTURE_TICKS_QUERY = gql`
  query FutureTicksQuery($tickCursor: Float, $ticksUntil: Float) {
    workspaceOrError {
      ... on Workspace {
        id
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
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
`;
