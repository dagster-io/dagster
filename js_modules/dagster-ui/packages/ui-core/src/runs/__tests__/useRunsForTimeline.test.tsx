import {MockedProvider} from '@apollo/client/testing';
import {waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
import {ReactNode} from 'react';

import {
  InstigationStatus,
  RepositoryLocationLoadStatus,
  RunStatus,
  buildDryRunInstigationTick,
  buildDryRunInstigationTicks,
  buildInstigationState,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildRepositoryOrigin,
  buildRun,
  buildRuns,
  buildSchedule,
  buildWorkspace,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {getMockResultFn} from '../../testing/mocking';
import {ONE_HOUR_S, getHourlyBuckets} from '../HourlyDataCache/HourlyDataCache';
import {
  COMPLETED_RUN_TIMELINE_QUERY,
  FUTURE_TICKS_QUERY,
  ONGOING_RUN_TIMELINE_QUERY,
  useRunsForTimeline,
} from '../useRunsForTimeline';

const mockCompletedRuns = (variables: any, result: any) => ({
  request: {
    query: COMPLETED_RUN_TIMELINE_QUERY,
    variables,
  },
  result,
});

const mockOngoingRuns = {
  request: {
    query: ONGOING_RUN_TIMELINE_QUERY,
    variables: {
      inProgressFilter: {statuses: ['CANCELING', 'STARTED']},
      cursor: undefined,
      limit: 500,
    },
  },
  result: {
    data: {
      ongoing: {
        __typename: 'Runs',
        results: [
          {
            id: '2',
            pipelineName: 'pipeline2',
            repositoryOrigin: {
              id: '2',
              repositoryName: 'repo2',
              repositoryLocationName: 'location2',
            },
            startTime: 1,
            endTime: 2,
            status: 'STARTED',
          },
        ],
      },
    },
  },
};

const mockFutureTicks = (start: number, end: number) => ({
  request: {
    query: FUTURE_TICKS_QUERY,
    variables: {
      tickCursor: start,
      ticksUntil: end,
    },
  },
  result: {
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
  },
});

describe('useRunsForTimeline', () => {
  it('fetches and processes run data correctly', async () => {
    const start = 0;
    const initialRange = [start, start + ONE_HOUR_S * 3] as const; // Example range in milliseconds
    const buckets = getHourlyBuckets(initialRange[0], initialRange[1]);
    expect(buckets).toHaveLength(3);
    const mocks = buckets.map((bucket, index) => {
      const [start, end] = bucket;
      const updatedBefore = end;
      const updatedAfter = start;
      return mockCompletedRuns(
        {
          completedFilter: {
            statuses: ['FAILURE', 'SUCCESS', 'CANCELED'],
            updatedBefore,
            updatedAfter,
          },
          cursor: undefined,
          limit: 500,
        },
        {
          data: {
            completed: {
              __typename: 'Runs',
              results: [
                {
                  id: `1-${index}`,
                  pipelineName: `pipeline${index}`,
                  repositoryOrigin: {
                    id: `1-${index}`,
                    repositoryName: 'repo1',
                    repositoryLocationName: 'repo1',
                  },
                  startTime: updatedAfter,
                  endTime: updatedBefore,
                  status: 'SUCCESS',
                },
              ],
            },
          },
        },
      );
    });

    mocks.push(mockOngoingRuns, mockFutureTicks(initialRange[0], initialRange[1]));

    const wrapper = ({children}: {children: ReactNode}) => (
      <MockedProvider mocks={mocks} addTypename={false}>
        {children}
      </MockedProvider>
    );

    const {result} = renderHook(
      () => useRunsForTimeline([initialRange[0] * 1000, initialRange[1] * 1000]),
      {
        wrapper,
      },
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.initialLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.jobs).toHaveLength(buckets.length);
    });

    expect(result.current.jobs[0]).toEqual({
      key: 'pipeline0-repo1@repo1',
      jobName: 'pipeline0',
      jobType: 'job',
      repoAddress: {name: 'repo1', location: 'repo1'},
      path: '/locations/repo1@repo1/jobs/pipeline0',
      runs: [
        {
          id: `1-0`,
          status: 'SUCCESS',
          startTime: buckets[0]![0] * 1000,
          endTime: buckets[0]![1] * 1000,
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
      mockOngoingRuns,
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
      () => useRunsForTimeline([interval[0] * 1000, interval[1] * 1000]),
      {
        wrapper,
      },
    );

    // Initial state
    expect(result.current.jobs).toEqual([]);
    expect(result.current.initialLoading).toBe(true);

    // Wait for the hook to update with initial interval data
    await waitFor(() => {
      expect(result.current.initialLoading).toBe(false);
    });

    // Verify the initial data
    expect(result.current.jobs).toHaveLength(1);
    expect(result.current.initialLoading).toBe(false);
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
});
