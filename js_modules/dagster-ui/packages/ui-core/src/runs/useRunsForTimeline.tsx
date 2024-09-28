import {useCallback, useContext, useLayoutEffect, useMemo, useRef, useState} from 'react';

import {HourlyDataCache, getHourlyBuckets} from './HourlyDataCache/HourlyDataCache';
import {doneStatuses} from './RunStatuses';
import {TimelineRow, TimelineRun} from './RunTimelineTypes';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {overlap} from './batchRunsForTimeline';
import {fetchPaginatedBucketData, fetchPaginatedData} from './fetchPaginatedBucketData';
import {getAutomationForRun} from './getAutomationForRun';
import {
  CompletedRunTimelineQuery,
  CompletedRunTimelineQueryVariables,
  CompletedRunTimelineQueryVersion,
  FutureTicksQuery,
  FutureTicksQueryVariables,
  OngoingRunTimelineQuery,
  OngoingRunTimelineQueryVariables,
  RunTimelineFragment,
} from './types/useRunsForTimeline.types';
import {QueryResult, gql, useApolloClient} from '../apollo-client';
import {AppContext} from '../app/AppContext';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {InstigationStatus, RunStatus, RunsFilter} from '../graphql/types';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
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
  showTicks = true,
}: {
  rangeMs: readonly [number, number];
  filter?: RunsFilter;
  refreshInterval?: number;
  batchLimit?: number;
  showTicks?: boolean;
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
  const completedRunsCache = useMemo(() => {
    if (filter) {
      return new HourlyDataCache<RunTimelineFragment>({
        id: localCacheIdPrefix ? `${localCacheIdPrefix}-useRunsForTimeline-filtered` : false,
        keyPrefix: JSON.stringify(filter),
        keyMaxCount: 3,
        version: CompletedRunTimelineQueryVersion,
      });
    }
    return new HourlyDataCache<RunTimelineFragment>({
      id: localCacheIdPrefix ? `${localCacheIdPrefix}-useRunsForTimeline` : false,
      version: CompletedRunTimelineQueryVersion,
    });
  }, [filter, localCacheIdPrefix]);
  const [completedRuns, setCompletedRuns] = useState<RunTimelineFragment[]>([]);

  useLayoutEffect(() => {
    // Fetch runs matching:
    // 1. updatedAfter (startSec) -> updatedBefore (endSec)
    // 2. updatedAfter (endSec) -> createdBefore (endSec).
    // For (2) we rely on the fact that runs are fetched in adjacent intervals from "now" going backwards
    // so we can assume a future bucket that is being or was fetched will have the runs we need.
    return completedRunsCache.subscribe(startSec, (runs) => {
      setCompletedRuns(
        runs.filter(
          (run) =>
            (run.startTime! <= endSec && run.updateTime! >= endSec) ||
            (run.updateTime! >= startSec && run.updateTime! <= endSec),
        ),
      );
    });
  }, [completedRunsCache, end, endSec, startSec]);

  const [completedRunsQueryData, setCompletedRunsData] = useState<{
    // TODO: Remove data property here since we grab the data from the cache instead of here.
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

  const {data: ongoingRunsData} = ongoingRunsQueryData;

  const [didLoadCache, setDidLoadCache] = useState(false);
  useBlockTraceUntilTrue('IndexedDBCache', didLoadCache);

  const fetchCompletedRunsQueryData = useCallback(async () => {
    await completedRunsCache.loadCacheFromIndexedDB();
    setDidLoadCache(true);

    // Accumulate the data to commit to the cache.
    // Intentionally don't commit until everything is done in order to avoid
    // committing incomplete data (and then assuming its full data later) in case the tab is closed early.
    const dataToCommitToCacheByBucket: WeakMap<
      [number, number],
      Array<{
        updatedBefore: number;
        updatedAfter: number;
        runs: RunTimelineFragment[];
      }>
    > = new WeakMap();

    return await fetchPaginatedBucketData({
      buckets: buckets
        .filter((bucket) => !completedRunsCache.isCompleteRange(bucket[0], bucket[1]))
        .map((bucket) => {
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

        if (completedRunsCache.isCompleteRange(updatedAfter, updatedBefore) && !cursor) {
          // If there's a cursor then that means the current range is being paginated so
          // it is not complete even though there is some data for the time range

          return {
            // TODO: Remove data property here
            data: [],
            cursor: undefined,
            hasMore: false,
            error: undefined,
          };
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
            data: [],
            cursor: undefined,
            hasMore: false,
            error: data.completed,
          };
        }
        const runs: RunTimelineFragment[] = data.completed.results;

        const hasMoreData = runs.length === batchLimit;
        const nextCursor = hasMoreData ? runs[runs.length - 1]!.id : undefined;

        const accumulatedData = dataToCommitToCacheByBucket.get(bucket) ?? [];
        dataToCommitToCacheByBucket.set(bucket, accumulatedData);

        if (hasMoreData) {
          // If there are runs lets accumulate this data to commit to the cache later
          // once all of the runs for this bucket have been fetched.
          accumulatedData.push({updatedAfter, updatedBefore, runs});
        } else {
          // If there is no more data lets commit all of the accumulated data to the cache
          completedRunsCache.addData(updatedAfter, updatedBefore, runs);
          accumulatedData.forEach(({updatedAfter, updatedBefore, runs}) => {
            completedRunsCache.addData(updatedAfter, updatedBefore, runs);
          });
        }

        return {
          data: [],
          cursor: nextCursor,
          hasMore: hasMoreData,
          error: undefined,
        };
      },
    });
  }, [batchLimit, buckets, client, completedRunsCache, runsFilter]);

  // If the user paginates backwards quickly then there will be multiple outstanding fetches
  // but we only want the most recent fetch to change loading back to false.
  // fetchIdRef will help us tell if this fetch is the most recent fetch.
  const fetchIdRef = useRef(0);
  const ongoingRunFetchIdRef = useRef(0);
  const futureTicksFetchIdRef = useRef(0);
  const fetchOngoingRunsQueryData = useCallback(async () => {
    const id = ++ongoingRunFetchIdRef.current;
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
      if (ongoingRunFetchIdRef.current === id) {
        setOngoingRunsData({
          data,
          loading: false,
          called: true,
          error: undefined,
        });
      }
    } catch (e) {
      if (ongoingRunFetchIdRef.current === id) {
        setOngoingRunsData(({data}) => ({
          data, // preserve existing data
          loading: false,
          called: true,
          error: e,
        }));
      }
    }
  }, [client, runsFilter, batchLimit]);

  const [futureTicksQueryData, setFutureTicksQueryData] = useState<
    Pick<QueryResult<FutureTicksQuery>, 'data' | 'error' | 'called' | 'loading'>
  >({data: undefined, called: true, loading: true, error: undefined});

  const fetchFutureTicks = useCallback(async () => {
    const id = ++futureTicksFetchIdRef.current;
    const queryData = await client.query<FutureTicksQuery, FutureTicksQueryVariables>({
      query: FUTURE_TICKS_QUERY,
      variables: showTicks
        ? {tickCursor: startSec, ticksUntil: _end / 1000.0}
        : {tickCursor: startSec, ticksUntil: startSec},
      fetchPolicy: 'no-cache',
    });
    if (id === futureTicksFetchIdRef.current) {
      setFutureTicksQueryData({...queryData, called: true});
    }
  }, [startSec, _end, client, showTicks]);

  useBlockTraceUntilTrue('CompletedRunTimelineQuery', !completedRunsQueryData.loading);

  const {data: futureTicksData} = futureTicksQueryData;

  const {workspaceOrError} = futureTicksData || {workspaceOrError: undefined};

  const [loading, setLoading] = useState(true);

  const previousRunsByJobKey = useRef<{
    jobInfo: Record<string, {repoAddress: RepoAddress; pipelineName: string; isAdHoc: boolean}>;
    runsByJobKey: {
      [jobKey: string]: {
        [id: string]: TimelineRun;
      };
    };
  }>({jobInfo: {}, runsByJobKey: {}});
  const {runsByJobKey, jobInfo} = useMemo(() => {
    if (loading) {
      // While we're loading data just keep returning the last result so that we're not
      // re-rendering 24+ times while we populate the cache asynchronously via our batching/chunking.
      return previousRunsByJobKey.current;
    }
    const jobInfo: Record<
      string,
      {repoAddress: RepoAddress; pipelineName: string; isAdHoc: boolean}
    > = {};
    const map: {
      [jobKey: string]: {
        [id: string]: TimelineRun;
      };
    } = {};
    const now = Date.now();

    function saveRunInfo(run: (typeof completedRuns)[0]) {
      if (run.startTime === null) {
        return;
      }

      // If the run has ended prior to the start of the range, discard it. This can occur
      // because we are using "updated" time for filtering our runs, which is a value
      // independent of start/end timestamps.
      if (run.endTime && run.endTime * 1000 < start) {
        return;
      }
      if (!run.repositoryOrigin) {
        return;
      }

      const repoAddress = buildRepoAddress(
        run.repositoryOrigin.repositoryName,
        run.repositoryOrigin.repositoryLocationName,
      );

      const runJobKey = makeJobKey(repoAddress, run.pipelineName);

      map[runJobKey] = map[runJobKey] || {};
      map[runJobKey]![run.id] = {
        id: run.id,
        status: run.status,
        startTime: run.startTime * 1000,
        endTime: run.endTime ? run.endTime * 1000 : now,
        automation: getAutomationForRun(repoAddress, run),
      };

      if (!jobInfo[runJobKey]) {
        const pipelineName = run.pipelineName;
        const isAdHoc = isHiddenAssetGroupJob(pipelineName);

        jobInfo[runJobKey] = {
          repoAddress,
          isAdHoc,
          pipelineName,
        };
      }
    }

    // fetch all the runs in the given range
    completedRuns.forEach(saveRunInfo);
    ongoingRunsData?.forEach(saveRunInfo);
    const current = {jobInfo, runsByJobKey: map};
    previousRunsByJobKey.current = current;
    return current;
  }, [loading, ongoingRunsData, completedRuns, start]);

  const jobsWithCompletedRunsAndOngoingRuns = useMemo(() => {
    const jobs: Record<string, TimelineRow> = {};
    if (!Object.keys(runsByJobKey).length) {
      return jobs;
    }

    Object.entries(runsByJobKey).forEach(([jobKey, jobRunsInfo]) => {
      const runs = Object.values(jobRunsInfo);
      const info = jobInfo[jobKey];
      if (!info) {
        return;
      }

      const {pipelineName, isAdHoc, repoAddress} = info;

      jobs[jobKey] = {
        key: jobKey,
        name: isAdHoc ? 'Ad hoc materializations' : pipelineName,
        type: isAdHoc ? 'asset' : 'job',
        repoAddress,
        path: isAdHoc
          ? null
          : workspacePipelinePath({
              repoName: repoAddress.name,
              repoLocation: repoAddress.location,
              pipelineName,
              isJob: true,
            }),
        runs,
      } as TimelineRow;
    });

    return jobs;
  }, [jobInfo, runsByJobKey]);

  const jobsWithCompletedRunsAndOngoingRunsValues = useMemo(() => {
    return Object.values(jobsWithCompletedRunsAndOngoingRuns);
  }, [jobsWithCompletedRunsAndOngoingRuns]);

  const unsortedJobs: TimelineRow[] = useMemo(() => {
    if (!workspaceOrError || workspaceOrError.__typename === 'PythonError' || _end < Date.now()) {
      return jobsWithCompletedRunsAndOngoingRunsValues;
    }
    const addedAdHocJobs = new Set();
    const jobs: TimelineRow[] = [];
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
                    automation: {type: 'schedule', repoAddress, name: schedule.name},
                  });
                }
              });
            }
          }

          const isAdHoc = isHiddenAssetGroupJob(pipeline.name);
          const jobKey = makeJobKey(repoAddress, pipeline.name);

          if (isAdHoc) {
            if (addedAdHocJobs.has(jobKey)) {
              continue;
            }
            addedAdHocJobs.add(jobKey);
          }

          const jobName = isAdHoc ? 'Ad hoc materializations' : pipeline.name;

          const jobRuns = Object.values(runsByJobKey[jobKey] || {});
          if (!jobTicks.length && !jobRuns.length) {
            continue;
          }

          const runs = [...jobRuns, ...jobTicks];

          let row = jobsWithCompletedRunsAndOngoingRuns[jobKey];
          if (row) {
            row = {...row, runs};
          } else {
            row = {
              key: jobKey,
              name: jobName,
              type: isAdHoc ? 'asset' : 'job',
              repoAddress,
              path: workspacePipelinePath({
                repoName: repoAddress.name,
                repoLocation: repoAddress.location,
                pipelineName: pipeline.name,
                isJob: pipeline.isJob,
              }),
              runs,
            } as TimelineRow;
          }

          jobs.push(row);
        }
      }
    }
    return jobs;
    // Don't add start/end time as a dependency here since it changes often.
    // Instead rely on the underlying runs changing in response to start/end changing
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    workspaceOrError,
    jobsWithCompletedRunsAndOngoingRunsValues,
    runsByJobKey,
    jobsWithCompletedRunsAndOngoingRuns,
  ]);

  const jobsWithRuns = useMemo(() => {
    const earliest = unsortedJobs.reduce(
      (accum, job) => {
        const startTimes = job.runs.map((job) => job.startTime);
        accum[job.key] = Math.min(...startTimes);
        return accum;
      },
      {} as {[jobKey: string]: number},
    );

    return unsortedJobs.sort((a, b) => earliest[a.key]! - earliest[b.key]!);
  }, [unsortedJobs]);

  const lastFetchRef = useRef({ongoing: 0, future: 0});
  const lastRangeMs = useRef([0, 0] as readonly [number, number]);
  if (Math.abs(lastRangeMs.current[0] - rangeMs[0]) > 30000) {
    lastFetchRef.current.future = 0;
  }
  lastRangeMs.current = rangeMs;

  const refreshState = useRefreshAtInterval({
    refresh: useCallback(async () => {
      const loadId = ++fetchIdRef.current;
      setLoading(true);
      await Promise.all([
        // Only fetch ongoing runs once every 30 seconds
        (async () => {
          if (lastFetchRef.current.ongoing < Date.now() - 30 * 1000) {
            await fetchOngoingRunsQueryData();
            lastFetchRef.current.ongoing = Date.now();
          }
        })(),
        // Only fetch future ticks once a minute
        (async () => {
          // If the the time range is in the past then future ticks are not visible on the timeline
          if (_end > Date.now() && lastFetchRef.current.future < Date.now() - 60 * 1000) {
            fetchFutureTicks();
          }
        })(),
        fetchCompletedRunsQueryData(),
      ]);
      if (loadId === fetchIdRef.current) {
        setLoading(false);
      }
    }, [fetchCompletedRunsQueryData, fetchFutureTicks, fetchOngoingRunsQueryData, _end]),
    intervalMs: refreshInterval,
    leading: true,
  });

  return {
    jobs: jobsWithRuns,
    loading,
    refreshState,
  };
};

export const makeJobKey = (repoAddress: RepoAddress, jobName: string) =>
  `${isHiddenAssetGroupJob(jobName) ? '__adhoc__' : jobName}-${repoAddressAsHumanString(
    repoAddress,
  )}`;

const RUN_TIMELINE_FRAGMENT = gql`
  fragment RunTimelineFragment on Run {
    id
    pipelineName
    tags {
      key
      value
    }
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
