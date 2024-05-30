import {QueryResult, gql, useApolloClient} from '@apollo/client';
import {useCallback, useContext, useLayoutEffect, useMemo, useRef, useState} from 'react';

import {HourlyDataCache, getHourlyBuckets} from './HourlyDataCache/HourlyDataCache';
import {doneStatuses} from './RunStatuses';
import {TimelineJob, TimelineRun} from './RunTimeline';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {overlap} from './batchRunsForTimeline';
import {fetchPaginatedBucketData, fetchPaginatedData} from './fetchPaginatedBucketData';
import {
  CompletedRunTimelineQuery,
  CompletedRunTimelineQueryVariables,
  FutureTicksQuery,
  FutureTicksQueryVariables,
  OngoingRunTimelineQuery,
  OngoingRunTimelineQueryVariables,
  RunTimelineFragment,
} from './types/useRunsForTimeline.types';
import {AppContext} from '../app/AppContext';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {InstigationStatus, RunStatus, RunsFilter} from '../graphql/types';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {useBlockTraceOnQueryResult} from '../performance/TraceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

const BATCH_LIMIT = 500;

export const useRunsForTimeline = ({
  rangeMs,
  filter,
  batchLimit = BATCH_LIMIT,
  refreshInterval = 2 * FIFTEEN_SECONDS,
}: {
  rangeMs: readonly [number, number];
  filter?: RunsFilter;
  refreshInterval?: number;
  batchLimit?: number;
}) => {
  const runsFilter = useMemo(() => {
    return filter ?? {};
  }, [filter]);
  const [start, _end] = rangeMs;
  const end = useMemo(() => {
    return Math.min(Date.now(), _end);
  }, [_end]);

  const startSec = start / 1000.0;
  const endSec = end / 1000.0;

  const buckets = useMemo(() => getHourlyBuckets(startSec, endSec), [startSec, endSec]);

  const client = useApolloClient();

  const {localCacheIdPrefix} = useContext(AppContext);
  const completedRunsCache = useMemo(
    () =>
      new HourlyDataCache<RunTimelineFragment>(
        localCacheIdPrefix ? `${localCacheIdPrefix}-useRunsForTimeline` : false,
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [runsFilter],
  );
  const [runsNotCapturedByUpdateBuckets, setRunsNotCapturedByUpdateBuckets] = useState<
    RunTimelineFragment[]
  >([]);

  useLayoutEffect(() => {
    // We fetch updatedAfter -> updatedBefore buckets but we also need runs that match
    // updatedAfter (right border) -> createdBefore (right border). Well we rely on the fact
    // that runs are fetched in adjacent intervals going to the past so we can assume a future bucket that
    // is being or was fetched will have that run so subscribe to future runs and filter for the ones createdBefore
    // our right boundary (endSec)
    return completedRunsCache.subscribe(endSec, (runs) => {
      setRunsNotCapturedByUpdateBuckets(runs.filter((run) => run.startTime! < endSec));
    });
  }, [completedRunsCache, end, endSec]);

  const [completedRunsQueryData, setCompletedRunsData] = useState<{
    data: RunTimelineFragment[] | undefined;
    loading: boolean;
    error: any;
    called: boolean;
  }>({
    data: undefined,
    loading: true,
    error: undefined,
    called: false,
  });
  const [ongoingRunsQueryData, setOngoingRunsData] = useState<{
    data: RunTimelineFragment[] | undefined;
    loading: boolean;
    error: any;
    called: boolean;
  }>({
    data: undefined,
    loading: true,
    error: undefined,
    called: false,
  });
  const {data: ongoingRunsData, loading: loadingOngoingRunsData} = ongoingRunsQueryData;
  const {data: completedRunsData, loading: loadingCompletedRunsData} = completedRunsQueryData;

  const fetchCompletedRunsQueryData = useCallback(async () => {
    await completedRunsCache.loadCacheFromIndexedDB();
    return await fetchPaginatedBucketData({
      buckets: buckets.map((bucket) => {
        let updatedAfter = bucket[0];
        let updatedBefore = bucket[1];
        const missingRange = completedRunsCache.getMissingIntervals(updatedAfter);
        if (missingRange[0]) {
          // When paginating backwards the missing range will be at the beginning of the hour
          // When looking the current time the missing range will be at the end of the hour
          updatedAfter = Math.max(missingRange[0][0], updatedAfter);
          updatedBefore = Math.min(missingRange[0][1], updatedBefore);
        }
        return [updatedAfter, updatedBefore] as [number, number];
      }),
      setQueryData: setCompletedRunsData,
      async fetchData(bucket, cursor: string | undefined) {
        const updatedBefore = bucket[1];
        const updatedAfter = bucket[0];
        let cacheData: RunTimelineFragment[] = [];

        if (completedRunsCache.isCompleteRange(updatedAfter, updatedBefore) && !cursor) {
          // If there's a cursor then that means the current range is being paginated so
          // it is not complete even though there is some data for the time range

          return {
            data: completedRunsCache.getHourData(updatedAfter),
            cursor: undefined,
            hasMore: false,
            error: undefined,
          };
        } else {
          cacheData = completedRunsCache.getHourData(updatedAfter);
        }

        const {data} = await client.query<
          CompletedRunTimelineQuery,
          CompletedRunTimelineQueryVariables
        >({
          query: COMPLETED_RUN_TIMELINE_QUERY,
          notifyOnNetworkStatusChange: true,
          fetchPolicy: 'no-cache',
          variables: {
            completedFilter: {
              ...runsFilter,
              statuses: Array.from(doneStatuses),
              updatedBefore,
              updatedAfter,
            },
            cursor,
            limit: batchLimit,
          },
        });

        if (data.completed.__typename !== 'Runs') {
          return {
            data: [...cacheData],
            cursor: undefined,
            hasMore: false,
            error: data.completed,
          };
        }
        const runs: RunTimelineFragment[] = data.completed.results;
        completedRunsCache.addData(updatedAfter, updatedBefore, runs);

        const hasMoreData = runs.length === batchLimit;
        const nextCursor = hasMoreData ? runs[runs.length - 1]!.id : undefined;

        return {
          data: [...cacheData, ...runs],
          cursor: nextCursor,
          hasMore: hasMoreData,
          error: undefined,
        };
      },
    });
  }, [batchLimit, buckets, client, completedRunsCache, runsFilter]);

  const fetchOngoingRunsQueryData = useCallback(async () => {
    setOngoingRunsData(({data}) => ({
      data, // preserve existing data
      loading: true,
      called: true,
      error: undefined,
    }));
    try {
      const data = await fetchPaginatedData({
        async fetchData(cursor: string | undefined) {
          const {data} = await client.query<
            OngoingRunTimelineQuery,
            OngoingRunTimelineQueryVariables
          >({
            query: ONGOING_RUN_TIMELINE_QUERY,
            notifyOnNetworkStatusChange: true,
            fetchPolicy: 'no-cache',
            variables: {
              inProgressFilter: {
                ...runsFilter,
                statuses: [RunStatus.CANCELING, RunStatus.STARTED],
              },
              cursor,
              limit: batchLimit,
            },
          });

          if (data.ongoing.__typename !== 'Runs') {
            return {
              data: [],
              cursor: undefined,
              hasMore: false,
              error: data.ongoing,
            };
          }
          const runs = data.ongoing.results;
          const hasMoreData = runs.length === batchLimit;
          const nextCursor = hasMoreData ? runs[runs.length - 1]!.id : undefined;
          return {
            data: runs,
            cursor: nextCursor,
            hasMore: hasMoreData,
            error: undefined,
          };
        },
      });
      setOngoingRunsData({
        data,
        loading: false,
        called: true,
        error: undefined,
      });
    } catch (e) {
      setOngoingRunsData(({data}) => ({
        data, // preserve existing data
        loading: false,
        called: true,
        error: e,
      }));
    }
  }, [client, runsFilter]);

  const [futureTicksQueryData, setFutureTicksQueryData] = useState<
    Pick<QueryResult<FutureTicksQuery>, 'data' | 'error' | 'called' | 'loading'>
  >({data: undefined, called: true, loading: true, error: undefined});

  const fetchFutureTicks = useCallback(async () => {
    const queryData = await client.query<FutureTicksQuery, FutureTicksQueryVariables>({
      query: FUTURE_TICKS_QUERY,
      variables: {tickCursor: startSec, ticksUntil: _end / 1000.0},
      fetchPolicy: 'no-cache',
    });
    setFutureTicksQueryData({...queryData, called: true});
  }, [startSec, _end, client]);

  useBlockTraceOnQueryResult(ongoingRunsQueryData, 'OngoingRunTimelineQuery');
  useBlockTraceOnQueryResult(completedRunsQueryData, 'CompletedRunTimelineQuery');
  useBlockTraceOnQueryResult(futureTicksQueryData, 'FutureTicksQuery');

  const {data: futureTicksData, loading: loadingFutureTicksData} = futureTicksQueryData;

  const {workspaceOrError} = futureTicksData || {workspaceOrError: undefined};

  const runsByJobKey = useMemo(() => {
    const map: {[jobKey: string]: TimelineRun[]} = {};
    const now = Date.now();

    // fetch all the runs in the given range
    [
      ...(ongoingRunsData ?? []),
      ...(completedRunsData ?? []),
      ...runsNotCapturedByUpdateBuckets,
    ].forEach((run) => {
      if (run.startTime === null) {
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
  }, [ongoingRunsData, completedRunsData, runsNotCapturedByUpdateBuckets, start, end]);

  const jobsWithRuns: TimelineJob[] = useMemo(() => {
    if (!workspaceOrError || workspaceOrError.__typename === 'PythonError') {
      return [];
    }

    const jobs: TimelineJob[] = [];
    for (const locationEntry of workspaceOrError.locationEntries) {
      if (
        !locationEntry.locationOrLoadError ||
        locationEntry.locationOrLoadError?.__typename === 'PythonError'
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
                if (
                  startTime > now &&
                  overlap({start, end: _end}, {start: startTime, end: startTime})
                ) {
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
            runs: [
              ...jobRuns.filter((run, idx, arr) => {
                // Runs can show up in multiple buckets due to the way were are filtering. Lets dedupe them for now
                // while we think of a better way to query while also caching.
                return arr.findIndex((bRun) => bRun.id === run.id) === idx;
              }),
              ...jobTicks,
            ],
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
  }, [workspaceOrError, runsByJobKey, start, _end]);

  const lastFetchRef = useRef({ongoing: 0, future: 0});
  const lastRangeMs = useRef([0, 0] as readonly [number, number]);
  if (Math.abs(lastRangeMs.current[0] - rangeMs[0]) > 30000) {
    lastFetchRef.current = {ongoing: 0, future: 0};
  }
  lastRangeMs.current = rangeMs;

  const refreshState = useRefreshAtInterval({
    refresh: useCallback(async () => {
      await Promise.all([
        // Only fetch ongoing runs once every 30 seconds
        (async () => {
          if (lastFetchRef.current.ongoing < Date.now() - 30 * 1000) {
            await fetchOngoingRunsQueryData();
            lastFetchRef.current.ongoing = Date.now();
          }
        })(),
        // Only fetch future ticks on a minute
        (async () => {
          if (lastFetchRef.current.future < Date.now() - 60 * 1000) {
            await fetchFutureTicks();
            lastFetchRef.current.future = Date.now();
          }
        })(),
        fetchCompletedRunsQueryData(),
      ]);
    }, [fetchCompletedRunsQueryData, fetchFutureTicks, fetchOngoingRunsQueryData]),
    intervalMs: refreshInterval,
    leading: true,
  });

  const initialLoading =
    (loadingOngoingRunsData && !ongoingRunsData) ||
    (loadingCompletedRunsData && !completedRunsQueryData) ||
    (loadingFutureTicksData && !futureTicksData) ||
    !workspaceOrError;

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

const RUN_TIMELINE_FRAGMENT = gql`
  fragment RunTimelineFragment on Run {
    id
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
    ...RunTimeFragment
  }
  ${RUN_TIME_FRAGMENT}
`;

export const ONGOING_RUN_TIMELINE_QUERY = gql`
  query OngoingRunTimelineQuery($inProgressFilter: RunsFilter!, $limit: Int!, $cursor: String) {
    ongoing: runsOrError(filter: $inProgressFilter, limit: $limit, cursor: $cursor) {
      ... on Runs {
        results {
          id
          ...RunTimelineFragment
        }
      }
    }
  }

  ${RUN_TIMELINE_FRAGMENT}
`;

export const COMPLETED_RUN_TIMELINE_QUERY = gql`
  query CompletedRunTimelineQuery($completedFilter: RunsFilter!, $limit: Int!, $cursor: String) {
    completed: runsOrError(filter: $completedFilter, limit: $limit, cursor: $cursor) {
      ... on Runs {
        results {
          id
          ...RunTimelineFragment
        }
      }
    }
  }

  ${RUN_TIMELINE_FRAGMENT}
`;

export const FUTURE_TICKS_QUERY = gql`
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
