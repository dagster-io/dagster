import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
import {ReactNode} from 'react';

import {AppContext, AppContextValue} from '../../app/AppContext';
import {
  InstigationStatus,
  RepositoryLocationLoadStatus,
  RunStatus,
  RunsFilter,
  buildDryRunInstigationTick,
  buildDryRunInstigationTicks,
  buildInstigationState,
  buildPipeline,
  buildPythonError,
  buildRepository,
  buildRepositoryLocation,
  buildRepositoryOrigin,
  buildRun,
  buildRuns,
  buildSchedule,
  buildWorkspace,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {ONE_HOUR_S, getHourlyBuckets} from '../HourlyDataCache/HourlyDataCache';
import {CompletedRunTimelineQueryVersion} from '../types/useRunsForTimeline.types';
import {
  COMPLETED_RUN_TIMELINE_QUERY,
  FUTURE_TICKS_QUERY,
  ONGOING_RUN_TIMELINE_QUERY,
  useRunsForTimeline,
} from '../useRunsForTimeline';

const mockedCache = {
  has: jest.fn(),
  get: jest.fn(),
  set: jest.fn(),
  constructorArgs: {},
};

jest.mock('idb-lru-cache', () => {
  return {
    cache: (...args: any[]) => {
      mockedCache.constructorArgs = args;
      return mockedCache;
    },
  };
});

const mockCompletedRuns = (variables: any, result: any) => ({
  request: {
    query: COMPLETED_RUN_TIMELINE_QUERY,
    variables,
  },
  result,
});

const defaultOngoingRun = buildRun({
  id: '2',
  pipelineName: 'pipeline2',
  repositoryOrigin: buildRepositoryOrigin({
    id: '2',
    repositoryName: 'repo2',
    repositoryLocationName: 'location2',
  }),
  startTime: 1,
  endTime: 2,
  status: RunStatus.STARTED,
});

const mockOngoingRuns = ({
  limit = 500,
  cursor,
  runsFilter,
  results = [defaultOngoingRun],
}: {
  limit?: number;
  results?: any[];
  cursor?: any;
  runsFilter?: RunsFilter;
} = {}) =>
  buildQueryMock({
    query: ONGOING_RUN_TIMELINE_QUERY,
    variables: {
      inProgressFilter: {
        statuses: ['CANCELING', 'STARTED'],
        ...runsFilter,
      },
      cursor,
      limit,
    },
    data: {
      ongoing: buildRuns({
        results,
      }),
    },
  });

const mockFutureTicks = (start: number, end: number) =>
  buildQueryMock({
    query: FUTURE_TICKS_QUERY,
    variables: {
      tickCursor: start,
      ticksUntil: end,
    },
    data: {
      workspaceOrError: buildWorkspace({
        locationEntries: [
          buildWorkspaceLocationEntry({
            id: '1',
            name: 'repo1',
            loadStatus: RepositoryLocationLoadStatus.LOADED,
            locationOrLoadError: buildRepositoryLocation({
              id: '1',
              name: 'repo1',
              repositories: [
                buildRepository({
                  id: '1',
                  name: 'repo1',
                  pipelines: new Array(4).fill(null).map((_, idx) =>
                    buildPipeline({
                      id: `${idx}`,
                      name: `pipeline${idx}`,
                      isJob: true,
                    }),
                  ),
                  schedules: [
                    buildSchedule({
                      id: '1',
                      name: 'schedule1',
                      pipelineName: 'pipeline1',
                      scheduleState: buildInstigationState({
                        id: '1',
                        status: InstigationStatus.RUNNING,
                      }),
                      futureTicks: buildDryRunInstigationTicks({
                        results: [
                          buildDryRunInstigationTick({
                            timestamp: 1624410000,
                          }),
                        ],
                      }),
                    }),
                  ],
                }),
              ],
            }),
          }),
        ],
      }),
    },
  });

function buildMocks(runsFilter?: RunsFilter) {
  const start = 0;
  const initialRange = [start, start + ONE_HOUR_S * 3] as const;
  const buckets = getHourlyBuckets(initialRange[0], initialRange[1]);
  expect(buckets).toHaveLength(3);

  const mocks: MockedResponse[] = buckets.map((bucket, index) => {
    const [start, end] = bucket;
    const updatedBefore = end;
    const updatedAfter = start;
    return mockCompletedRuns(
      {
        completedFilter: {
          statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
          updatedBefore,
          updatedAfter,
          ...runsFilter,
        },
        cursor: undefined,
        limit: 500,
      },
      {
        data: {
          completed: buildRuns({
            results: [
              buildRun({
                id: `1-${index}`,
                pipelineName: `pipeline${index}`,
                repositoryOrigin: buildRepositoryOrigin({
                  id: `1-${index}`,
                  repositoryName: 'repo1',
                  repositoryLocationName: 'repo1',
                }),
                startTime: updatedAfter,
                endTime: updatedBefore,
                status: RunStatus.SUCCESS,
              }),
            ],
          }),
        },
      },
    );
  });

  mocks.push(mockOngoingRuns({runsFilter}), mockFutureTicks(initialRange[0], initialRange[1]));

  return {mocks, buckets, initialRange};
}

const contextWithCacheId: AppContextValue = {
  localCacheIdPrefix: 'test',
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
};

describe('useRunsForTimeline', () => {
  it('fetches and processes run data correctly', async () => {
    const {mocks, buckets, initialRange} = buildMocks();
    const wrapper = ({children}: {children: ReactNode}) => (
      <MockedProvider mocks={mocks} addTypename={false}>
        {children}
      </MockedProvider>
    );

    const {result} = renderHook(
      () => useRunsForTimeline({rangeMs: [initialRange[0] * 1000, initialRange[1] * 1000]}),
      {wrapper},
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      // Add 1 for the ongoing run
      expect(result.current.jobs).toHaveLength(buckets.length + 1);
    });

    const pipeline0 = result.current.jobs.find((job) => job.name === 'pipeline0');

    expect(pipeline0).toEqual({
      key: 'pipeline0-repo1@repo1',
      name: 'pipeline0',
      type: 'job',
      repoAddress: {name: 'repo1', location: 'repo1'},
      path: '/locations/repo1@repo1/jobs/pipeline0',
      runs: [
        {
          id: `1-0`,
          status: RunStatus.SUCCESS,
          startTime: buckets[0]![0] * 1000,
          endTime: buckets[0]![1] * 1000,
          automation: null,
        },
      ],
    });
  });

  it('requests only missing intervals considering hourly buckets', async () => {
    const start = 0;
    const initialInterval = [start, start + ONE_HOUR_S] as const; // Initial interval to populate the cache
    const extendedInterval = [start, start + ONE_HOUR_S * 3] as const; // Extended interval to test missing segment request

    let interval: readonly [number, number] = initialInterval;

    const initialBuckets = getHourlyBuckets(initialInterval[0], initialInterval[1]);
    const extendedBuckets = getHourlyBuckets(extendedInterval[0], extendedInterval[1]); // Remove the first bucket since it was already fetched.

    expect(initialBuckets).toHaveLength(1);
    expect(extendedBuckets).toHaveLength(3);

    const initialCompletedRunsVariables = initialBuckets.map((bucket) => ({
      completedFilter: {
        statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
        updatedBefore: bucket[1],
        updatedAfter: bucket[0],
      },
      cursor: undefined,
      limit: 500,
    }));

    const extendedCompletedRunsVariables = extendedBuckets.map((bucket) => ({
      completedFilter: {
        statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
        updatedBefore: bucket[1],
        updatedAfter: bucket[0],
      },
      cursor: undefined,
      limit: 500,
    }));

    const initialCompletedRunsResult = {
      data: {
        completed: buildRuns({
          results: [
            buildRun({
              id: '1',
              pipelineName: 'pipeline1',
              repositoryOrigin: buildRepositoryOrigin({
                id: '1',
                repositoryName: 'repo1',
                repositoryLocationName: 'repo1',
              }),
              startTime: initialInterval[0],
              endTime: initialInterval[1],
              updateTime: initialInterval[1],
              status: RunStatus.SUCCESS,
            }),
          ],
        }),
      },
    };

    const extendedCompletedRunsResult = {
      data: {
        completed: buildRuns({
          results: [
            buildRun({
              id: '2',
              pipelineName: 'pipeline2',
              repositoryOrigin: buildRepositoryOrigin({
                id: '2',
                repositoryName: 'repo2',
                repositoryLocationName: 'location2',
              }),
              startTime: extendedInterval[0],
              endTime: extendedInterval[1],
              updateTime: extendedInterval[1],
              status: RunStatus.SUCCESS,
            }),
          ],
        }),
      },
    };

    const initialMocks = initialCompletedRunsVariables.map((variables) =>
      mockCompletedRuns(variables, initialCompletedRunsResult),
    );

    const extendedMocks = extendedCompletedRunsVariables.map((variables) =>
      mockCompletedRuns(variables, extendedCompletedRunsResult),
    );
    const extendedMockResultFns = extendedMocks.map((mock) => getMockResultFn(mock));

    const mocks = [
      ...initialMocks,
      ...extendedMocks,
      mockOngoingRuns(),
      mockFutureTicks(initialInterval[0], initialInterval[1]),
      mockFutureTicks(extendedInterval[0], extendedInterval[1]),
    ];

    const wrapper = ({children}: {children?: ReactNode}) => (
      <MockedProvider mocks={mocks} addTypename={false}>
        {children}
      </MockedProvider>
    );

    // Render hook with initial interval to populate the cache
    const {result, rerender} = renderHook(
      () => useRunsForTimeline({rangeMs: [interval[0] * 1000, interval[1] * 1000]}),
      {wrapper},
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.loading).toBe(true);

    // Wait for the hook to update with initial interval data
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Verify the initial data
    expect(result.current.jobs).toHaveLength(2);
    expect(result.current.loading).toBe(false);
    expect(result.current.jobs[0]!.runs).toHaveLength(1);

    // Rerender hook with extended interval
    interval = extendedInterval;
    rerender();

    // Wait for the hook to update with extended interval data
    await waitFor(() => {
      // This bucket was not called because it was already fettched;
      expect(extendedMockResultFns[0]).not.toHaveBeenCalled();
      extendedMockResultFns.slice(1).forEach((mock) => {
        expect(mock).toHaveBeenCalled();
      });
    });
  });

  it('paginates a bucket correctly', async () => {
    const start = 0;
    const interval = [start, start + ONE_HOUR_S] as const;
    const buckets = getHourlyBuckets(interval[0], interval[1]);
    expect(buckets).toHaveLength(1);

    const bucket = buckets[0]!;
    const updatedBefore = bucket[1];
    const updatedAfter = bucket[0];

    const mockPaginatedRuns = ({cursor, result}: {cursor?: string | undefined; result: any}) => ({
      request: {
        query: COMPLETED_RUN_TIMELINE_QUERY,
        variables: {
          completedFilter: {
            statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
            updatedBefore,
            updatedAfter,
          },
          cursor,
          limit: 1,
        },
      },
      result,
    });

    const firstPageResult = {
      data: {
        completed: buildRuns({
          results: [
            buildRun({
              id: '1-1',
              pipelineName: 'pipeline1',
              repositoryOrigin: buildRepositoryOrigin({
                id: '1-1',
                repositoryName: 'repo1',
                repositoryLocationName: 'repo1',
              }),
              startTime: updatedAfter,
              endTime: updatedBefore,
              updateTime: updatedBefore,
              status: RunStatus.SUCCESS,
            }),
          ],
        }),
      },
    };

    const secondPageResult = {
      data: {
        completed: buildRuns({
          results: [
            buildRun({
              id: '1-2',
              pipelineName: 'pipeline1',
              repositoryOrigin: buildRepositoryOrigin({
                id: '1-1',
                repositoryName: 'repo1',
                repositoryLocationName: 'repo1',
              }),
              startTime: updatedAfter,
              endTime: updatedBefore,
              updateTime: updatedBefore,
              status: RunStatus.SUCCESS,
            }),
          ],
        }),
      },
    };

    const thirdPageResult = {
      data: {
        completed: buildRuns({
          results: [],
        }),
      },
    };

    const mocks = [
      mockPaginatedRuns({result: firstPageResult}),
      mockPaginatedRuns({cursor: '1-1', result: secondPageResult}),
      mockPaginatedRuns({cursor: '1-2', result: thirdPageResult}),
      mockOngoingRuns({limit: 1}),
      mockOngoingRuns({limit: 1, results: [], cursor: '2'}),
    ];

    const mockCbs = mocks.map(getMockResultFn);

    const wrapper = ({children}: {children: ReactNode}) => (
      <MockedProvider mocks={mocks} addTypename={false}>
        {children}
      </MockedProvider>
    );

    const {result} = renderHook(
      () => useRunsForTimeline({rangeMs: [interval[0] * 1000, interval[1] * 1000], batchLimit: 1}),
      {wrapper},
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.jobs).toHaveLength(2);
    });

    expect(result.current.jobs[0]!.runs).toHaveLength(2);

    expect(result.current.jobs[0]!.runs[0]).toEqual({
      id: '1-1',
      status: 'SUCCESS',
      startTime: buckets[0]![0] * 1000,
      endTime: buckets[0]![1] * 1000,
      automation: null,
    });

    expect(result.current.jobs[0]!.runs[1]).toEqual({
      id: '1-2',
      status: 'SUCCESS',
      startTime: buckets[0]![0] * 1000,
      endTime: buckets[0]![1] * 1000,
      automation: null,
    });

    mockCbs.forEach((mockFn) => {
      expect(mockFn).toHaveBeenCalled();
    });
  });

  it('uses cached data from indexedb and only requests missing interval and combines the cached data with the fetched data', async () => {
    const sixDaysAgo = Date.now() / 1000 - 6 * 24 * 60 * 60;
    const start = Math.floor(sixDaysAgo / ONE_HOUR_S) * ONE_HOUR_S;
    const initialRange = [start, start + ONE_HOUR_S] as const;
    const buckets = getHourlyBuckets(initialRange[0], initialRange[1]);
    expect(buckets).toHaveLength(1);

    const cachedRange = [start, start + ONE_HOUR_S / 2] as const;

    const mocks: MockedResponse[] = [
      mockCompletedRuns(
        {
          completedFilter: {
            statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
            // We only fetch the range missing from the cache
            updatedBefore: initialRange[1],
            updatedAfter: cachedRange[1],
          },
          cursor: undefined,
          limit: 500,
        },
        {
          data: {
            completed: buildRuns({
              results: [
                buildRun({
                  id: `1-0`,
                  pipelineName: `pipeline0`,
                  repositoryOrigin: buildRepositoryOrigin({
                    id: `1-0`,
                    repositoryName: 'repo1',
                    repositoryLocationName: 'repo1',
                  }),
                  startTime: initialRange[0],
                  endTime: initialRange[1],
                  updateTime: initialRange[1],
                  status: RunStatus.SUCCESS,
                }),
              ],
            }),
          },
        },
      ),
    ];

    mocks.push(mockOngoingRuns({results: []}), mockFutureTicks(initialRange[0], initialRange[1]));

    const wrapper = ({children}: {children: ReactNode}) => (
      <AppContext.Provider value={contextWithCacheId}>
        <MockedProvider mocks={mocks} addTypename={false}>
          {children}
        </MockedProvider>
      </AppContext.Provider>
    );

    mockedCache.has.mockResolvedValue(true);

    const startHour = Math.floor(start / ONE_HOUR_S);
    mockedCache.get.mockResolvedValue({
      value: {
        version: CompletedRunTimelineQueryVersion,
        cache: new Map([
          [
            startHour,
            [
              {
                start: cachedRange[0],
                end: cachedRange[1],
                data: [
                  buildRun({
                    id: 'cached-run',
                    pipelineName: 'pipeline0',
                    repositoryOrigin: buildRepositoryOrigin({
                      id: '1-1',
                      repositoryName: 'repo1',
                      repositoryLocationName: 'repo1',
                    }),
                    startTime: initialRange[0],
                    endTime: initialRange[1],
                    updateTime: initialRange[1],
                    status: RunStatus.SUCCESS,
                  }),
                ],
              },
            ],
          ],
        ]),
      },
    });

    const {result} = renderHook(
      () => useRunsForTimeline({rangeMs: [initialRange[0] * 1000, initialRange[1] * 1000]}),
      {
        wrapper,
      },
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.jobs).toHaveLength(1);
    });

    expect(result.current.jobs.find((job) => job.name === 'pipeline0')).toEqual({
      key: 'pipeline0-repo1@repo1',
      name: 'pipeline0',
      type: 'job',
      repoAddress: {name: 'repo1', location: 'repo1'},
      path: '/locations/repo1@repo1/jobs/pipeline0',
      runs: [
        {
          endTime: initialRange[1] * 1000,
          id: 'cached-run',
          startTime: initialRange[0] * 1000,
          status: RunStatus.SUCCESS,
          automation: null,
        },
        {
          endTime: initialRange[1] * 1000,
          id: '1-0',
          startTime: initialRange[0] * 1000,
          status: RunStatus.SUCCESS,
          automation: null,
        },
      ],
    });
  });

  it('uses the main cache when no filters are provided', async () => {
    const {mocks, initialRange} = buildMocks();

    const wrapper = ({children}: {children: ReactNode}) => (
      <AppContext.Provider value={contextWithCacheId}>
        <MockedProvider mocks={mocks} addTypename={false}>
          {children}
        </MockedProvider>
      </AppContext.Provider>
    );

    renderHook(
      () => useRunsForTimeline({rangeMs: [initialRange[0] * 1000, initialRange[1] * 1000]}),
      {wrapper},
    );

    await waitFor(() => {
      expect(mockedCache.constructorArgs).toEqual([
        {dbName: 'HourlyDataCache:test-useRunsForTimeline', maxCount: 1},
      ]);
      expect(mockedCache.set).toHaveBeenCalled();
    });
  });

  it('uses the filtered cache when filters are provided', async () => {
    const {mocks, initialRange} = buildMocks({
      tags: [{key: 'dagster/backfill_id', value: '1234'}],
    });

    const wrapper = ({children}: {children: ReactNode}) => (
      <AppContext.Provider value={contextWithCacheId}>
        <MockedProvider mocks={mocks} addTypename={false}>
          {children}
        </MockedProvider>
      </AppContext.Provider>
    );

    const props = {
      rangeMs: [initialRange[0] * 1000, initialRange[1] * 1000] as [number, number],
      filter: {tags: [{key: 'dagster/backfill_id', value: '1234'}]},
    };
    renderHook(() => useRunsForTimeline(props), {wrapper});

    await waitFor(() => {
      expect(mockedCache.constructorArgs).toEqual([
        {dbName: 'HourlyDataCache:test-useRunsForTimeline-filtered', maxCount: 3},
      ]);
      expect(mockedCache.set).toHaveBeenCalled();
    });
  });

  it('does not commit data to the cache if a paginated bucket is not fully fetched', async () => {
    const start = 0;
    const interval = [start, start + ONE_HOUR_S] as const;
    const buckets = getHourlyBuckets(interval[0], interval[1]);
    expect(buckets).toHaveLength(1);

    const bucket = buckets[0]!;
    const updatedBefore = bucket[1];
    const updatedAfter = bucket[0];

    const mockPaginatedRuns = ({cursor, result}: {cursor?: string | undefined; result: any}) => ({
      request: {
        query: COMPLETED_RUN_TIMELINE_QUERY,
        variables: {
          completedFilter: {
            statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
            updatedBefore,
            updatedAfter,
          },
          cursor,
          limit: 1,
        },
      },
      result,
    });

    const firstPageResult = {
      data: {
        completed: buildRuns({
          results: [
            buildRun({
              id: '1-1',
              pipelineName: 'pipeline1',
              repositoryOrigin: buildRepositoryOrigin({
                id: '1-1',
                repositoryName: 'repo1',
                repositoryLocationName: 'repo1',
              }),
              startTime: updatedAfter,
              endTime: updatedBefore,
              updateTime: updatedBefore,
              status: RunStatus.SUCCESS,
            }),
          ],
        }),
      },
    };

    // Throw an error when fetching the second page
    const secondPageResult = {
      data: {
        completed: buildPythonError(),
      },
    };

    const mocks = [
      mockPaginatedRuns({result: firstPageResult}),
      mockPaginatedRuns({cursor: '1-1', result: secondPageResult}),
    ];

    const wrapper = ({children}: {children: ReactNode}) => (
      <AppContext.Provider value={contextWithCacheId}>
        <MockedProvider mocks={mocks} addTypename={false}>
          {children}
        </MockedProvider>
      </AppContext.Provider>
    );

    const {result} = renderHook(
      () => useRunsForTimeline({rangeMs: [interval[0] * 1000, interval[1] * 1000], batchLimit: 1}),
      {wrapper},
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.jobs).toHaveLength(0);
    });

    expect(mockedCache.set).not.toHaveBeenCalled();
  });
});
