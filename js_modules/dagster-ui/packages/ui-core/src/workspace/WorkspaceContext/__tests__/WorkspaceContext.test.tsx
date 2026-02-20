jest.useFakeTimers();

import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, renderHook, waitFor} from '@testing-library/react';
import {useContext} from 'react';
import {RecoilRoot} from 'recoil';

import {AppContext} from '../../../app/AppContext';
import {
  buildPythonError,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../../graphql/types';
import {KEY_PREFIX, __resetForJest} from '../../../search/useIndexedDBCachedQuery';
import {getMockResultFn} from '../../../testing/mocking';
import {cache} from '../../../util/idb-lru-cache';
import {WorkspaceContext, WorkspaceProvider} from '../WorkspaceContext';
import {LOCATION_WORKSPACE_ASSETS_QUERY_KEY} from '../WorkspaceLocationAssetsFetcher';
import {LOCATION_WORKSPACE_QUERY_KEY} from '../WorkspaceLocationDataFetcher';
import {CODE_LOCATION_STATUS_QUERY_KEY} from '../WorkspaceStatusPoller';
import {buildWorkspaceMocks} from '../__fixtures__/Workspace.fixtures';
import {
  CodeLocationStatusQueryVersion,
  LocationWorkspaceAssetsQueryVersion,
  LocationWorkspaceQueryVersion,
} from '../types/WorkspaceQueries.types';
import {repoLocationToRepos} from '../util';

const mockCache = cache as any;

const mockedCacheStore: Record<string, any> = {};

jest.mock('../../../util/idb-lru-cache', () => {
  return {
    cache: jest.fn(({dbName}) => {
      if (!mockedCacheStore[dbName]) {
        mockedCacheStore[dbName] = {
          has: jest.fn(),
          get: jest.fn(),
          set: jest.fn(),
          delete: jest.fn(),
        };
      }
      return mockedCacheStore[dbName];
    }),
  };
});

const mockLoadFromServerQueue: (() => void)[] = [];
function drainMockLoadFromServerQueue() {
  while (mockLoadFromServerQueue.length) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    mockLoadFromServerQueue.shift()!();
  }
}
const mockHandleStatusUpdateQueue: (() => void)[] = [];
function drainMockHandleStatusUpdateQueue() {
  while (mockHandleStatusUpdateQueue.length) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    mockHandleStatusUpdateQueue.shift()!();
  }
}
jest.mock('../../../workspace/WorkspaceContext/TimingControls', () => {
  return {
    TimingControls: {
      loadFromServer: (fn: () => void) => {
        mockLoadFromServerQueue.push(fn);
      },
      handleStatusUpdate: (fn: () => void) => {
        mockHandleStatusUpdateQueue.push(fn);
      },
    },
  };
});

afterEach(async () => {
  jest.resetModules();
  jest.clearAllMocks();
  jest.clearAllTimers();
  __resetForJest();
});
const LOCAL_CACHE_ID_PREFIX = 'test';
function renderWithMocks(mocks: MockedResponse[]) {
  return renderHook(() => useContext(WorkspaceContext), {
    wrapper({children}) {
      return (
        <RecoilRoot>
          <AppContext.Provider
            value={{
              localCacheIdPrefix: LOCAL_CACHE_ID_PREFIX,
              basePath: '',
              rootServerURI: '',
              telemetryEnabled: false,
            }}
          >
            <MockedProvider mocks={mocks}>
              <WorkspaceProvider>{children}</WorkspaceProvider>
            </MockedProvider>
          </AppContext.Provider>
        </RecoilRoot>
      );
    },
  });
}

function getLocationMocks(updatedTimestamp = 0) {
  const repositoryLocation1 = buildRepositoryLocation({
    repositories: [buildRepository(), buildRepository()],
  });
  const repositoryLocation2 = buildRepositoryLocation({
    repositories: [buildRepository(), buildRepository()],
  });
  const repositoryLocation3 = buildRepositoryLocation({
    repositories: [buildRepository(), buildRepository()],
  });
  const location1 = buildWorkspaceLocationEntry({
    name: 'location1',
    updatedTimestamp,
    versionKey: String(updatedTimestamp),
    locationOrLoadError: repositoryLocation1,
  });
  const location2 = buildWorkspaceLocationEntry({
    name: 'location2',
    updatedTimestamp,
    versionKey: String(updatedTimestamp),
    locationOrLoadError: repositoryLocation2,
  });

  const location3 = buildWorkspaceLocationEntry({
    name: 'location3',
    updatedTimestamp,
    versionKey: String(updatedTimestamp),
    locationOrLoadError: repositoryLocation3,
  });

  return {
    repositoryLocation1,
    repositoryLocation2,
    repositoryLocation3,
    location1,
    location2,
    location3,
    caches: {
      codeLocationStatusQuery: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${CODE_LOCATION_STATUS_QUERY_KEY}`,
      }),
      location1: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${LOCATION_WORKSPACE_QUERY_KEY}/location1`,
      }),
      location2: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${LOCATION_WORKSPACE_QUERY_KEY}/location2`,
      }),
      location3: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${LOCATION_WORKSPACE_QUERY_KEY}/location3`,
      }),
      location1Assets: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${LOCATION_WORKSPACE_ASSETS_QUERY_KEY}/location1`,
      }),
      location2Assets: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${LOCATION_WORKSPACE_ASSETS_QUERY_KEY}/location2`,
      }),
      location3Assets: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${LOCATION_WORKSPACE_ASSETS_QUERY_KEY}/location3`,
      }),
    },
  };
}

describe('WorkspaceContext', () => {
  it('Fetches by code location when cache is empty', async () => {
    const {
      location1,
      location2,
      location3,
      repositoryLocation1,
      repositoryLocation2,
      repositoryLocation3,
      caches,
    } = getLocationMocks(-1);
    caches.codeLocationStatusQuery.has.mockResolvedValue(false);
    caches.location1.has.mockResolvedValue(false);
    caches.location2.has.mockResolvedValue(false);
    caches.location3.has.mockResolvedValue(false);
    caches.location1Assets.has.mockResolvedValue(false);
    caches.location2Assets.has.mockResolvedValue(false);
    caches.location3Assets.has.mockResolvedValue(false);
    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});
    const mockCbs = mocks.map(getMockResultFn);

    // Include code location status mock a second time since we call runOnlyPendingTimersAsync twice
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const {result} = renderWithMocks([...mocks, mocks[0]!]);

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
    expect(result.current.loadingNonAssets).toEqual(true);
    expect(result.current.loadingAssets).toEqual(true);

    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
      drainMockHandleStatusUpdateQueue();
    });

    // First mock is the code location status query
    expect(mockCbs[0]).toHaveBeenCalled();
    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();
    expect(mockCbs[3]).not.toHaveBeenCalled();
    expect(mockCbs[4]).not.toHaveBeenCalled();
    expect(mockCbs[5]).not.toHaveBeenCalled();
    expect(mockCbs[6]).not.toHaveBeenCalled();

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
    expect(result.current.loadingNonAssets).toEqual(true);
    expect(result.current.loadingAssets).toEqual(true);

    // Runs the individual location queries
    await act(async () => {
      drainMockLoadFromServerQueue();
    });

    await waitFor(() => {
      expect(mockCbs[1]).toHaveBeenCalled();
      expect(mockCbs[2]).toHaveBeenCalled();
      expect(mockCbs[3]).toHaveBeenCalled();
      expect(mockCbs[4]).toHaveBeenCalled();
      expect(mockCbs[5]).toHaveBeenCalled();
      expect(mockCbs[6]).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });
    expect(result.current.allRepos).toEqual([
      ...repoLocationToRepos(repositoryLocation1),
      ...repoLocationToRepos(repositoryLocation2),
      ...repoLocationToRepos(repositoryLocation3),
    ]);
    expect(result.current.data).toEqual({
      [location1.name]: location1,
      [location2.name]: location2,
      [location3.name]: location3,
    });

    await act(async () => {
      // Exhaust any remaining tasks so they don't affect the next test.
      await jest.runAllTicks();
    });
  });

  it('Uses cache if it is up to date and does not query by location', async () => {
    const {
      location1,
      location2,
      location3,
      repositoryLocation1,
      repositoryLocation2,
      repositoryLocation3,
      caches,
    } = getLocationMocks();
    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});

    caches.codeLocationStatusQuery.has.mockResolvedValue(true);
    caches.codeLocationStatusQuery.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[0]! as any).result.data, version: CodeLocationStatusQueryVersion},
    });
    caches.location1.has.mockResolvedValue(true);
    caches.location1.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[1]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location2.has.mockResolvedValue(true);
    caches.location2.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[2]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location3.has.mockResolvedValue(true);
    caches.location3.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[3]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location1Assets.has.mockResolvedValue(true);
    caches.location1Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[4]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    caches.location2Assets.has.mockResolvedValue(true);
    caches.location2Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[5]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    caches.location3Assets.has.mockResolvedValue(true);
    caches.location3Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[6]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });

    const mockCbs = mocks.map(getMockResultFn);

    const {result} = renderWithMocks([...mocks]);

    await waitFor(async () => {
      drainMockLoadFromServerQueue();
      drainMockHandleStatusUpdateQueue();
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });
    // We queries for code location statuses but saw we were up to date
    // so we didn't call any the location queries
    expect(mockCbs[0]).toHaveBeenCalled();

    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();
    expect(mockCbs[3]).not.toHaveBeenCalled();
    expect(mockCbs[4]).not.toHaveBeenCalled();
    expect(mockCbs[5]).not.toHaveBeenCalled();
    expect(mockCbs[6]).not.toHaveBeenCalled();
    expect(result.current.allRepos).toEqual([
      ...repoLocationToRepos(repositoryLocation1),
      ...repoLocationToRepos(repositoryLocation2),
      ...repoLocationToRepos(repositoryLocation3),
    ]);
    expect(result.current.data).toEqual({
      [location1.name]: location1,
      [location2.name]: location2,
      [location3.name]: location3,
    });

    await act(async () => {
      // Exhaust any remaining tasks so they don't affect the next test.
      await jest.runAllTicks();
    });
  });

  it('returns cached data, detects its out of date and queries by location to update it', async () => {
    const {
      location1,
      location2,
      location3,
      repositoryLocation1,
      repositoryLocation2,
      repositoryLocation3,
      caches,
    } = getLocationMocks(-3);
    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});
    const {
      location1: updatedLocation1,
      location2: updatedLocation2,
      location3: updatedLocation3,
    } = getLocationMocks(1);

    const updatedMocks = buildWorkspaceMocks(
      [updatedLocation1, updatedLocation2, updatedLocation3],
      {delay: 10},
    );

    caches.codeLocationStatusQuery.has.mockResolvedValue(true);
    caches.codeLocationStatusQuery.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[0]! as any).result.data, version: CodeLocationStatusQueryVersion},
    });
    caches.location1.has.mockResolvedValue(true);
    caches.location1.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[1]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location2.has.mockResolvedValue(true);
    caches.location2.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[2]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location3.has.mockResolvedValue(true);
    caches.location3.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[3]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location1Assets.has.mockResolvedValue(true);
    caches.location1Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[4]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    caches.location2Assets.has.mockResolvedValue(true);
    caches.location2Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[5]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    caches.location3Assets.has.mockResolvedValue(true);
    caches.location3Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[6]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    const mockCbs = updatedMocks.map(getMockResultFn);

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const {result} = renderWithMocks([...updatedMocks, updatedMocks[0]!]);

    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();
    });
    // We queries for code location statuses and we see we are not up to date yet so the current data is still equal to the cached data
    expect(mockCbs[0]).toHaveBeenCalled();
    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();
    expect(mockCbs[3]).not.toHaveBeenCalled();
    expect(mockCbs[4]).not.toHaveBeenCalled();
    expect(mockCbs[5]).not.toHaveBeenCalled();
    expect(mockCbs[6]).not.toHaveBeenCalled();
    expect(result.current.allRepos).toEqual([
      ...repoLocationToRepos(repositoryLocation1),
      ...repoLocationToRepos(repositoryLocation2),
      ...repoLocationToRepos(repositoryLocation3),
    ]);
    expect(result.current.data).toEqual({
      [location1.name]: location1,
      [location2.name]: location2,
      [location3.name]: location3,
    });

    // Run the location queries and wait for the location queries to return
    await act(async () => {
      drainMockLoadFromServerQueue();
    });

    await waitFor(() => {
      expect(result.current.data).toEqual({
        [location1.name]: updatedLocation1,
        [location2.name]: updatedLocation2,
        [location3.name]: updatedLocation3,
      });
    });

    expect(updatedLocation1).not.toEqual(location1);

    await act(async () => {
      // Exhaust any remaining tasks so they don't affect the next test.
      await jest.runAllTicks();
    });
  });

  it('Detects and deletes removed code locations from cache', async () => {
    const {
      location1,
      location2,
      location3,
      repositoryLocation1,
      repositoryLocation2,
      repositoryLocation3,
      caches,
    } = getLocationMocks(0);
    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});
    const {location1: updatedLocation1, location2: updatedLocation2} = getLocationMocks(1);

    // Remove location 3
    const updatedMocks = buildWorkspaceMocks([updatedLocation1, updatedLocation2], {delay: 10});

    caches.codeLocationStatusQuery.has.mockResolvedValue(true);
    caches.codeLocationStatusQuery.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[0]! as any).result.data, version: CodeLocationStatusQueryVersion},
    });
    caches.location1.has.mockResolvedValue(true);
    caches.location1.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[1]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location2.has.mockResolvedValue(true);
    caches.location2.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[2]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location3.has.mockResolvedValue(true);
    caches.location3.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[3]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location1Assets.has.mockResolvedValue(true);
    caches.location1Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[4]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    caches.location2Assets.has.mockResolvedValue(true);
    caches.location2Assets.get.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value: {data: (mocks[5]! as any).result.data, version: LocationWorkspaceAssetsQueryVersion},
    });
    const mockCbs = updatedMocks.map(getMockResultFn);

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const {result} = renderWithMocks([...updatedMocks, updatedMocks[0]!]);

    await act(async () => {
      await jest.runAllTicks();
      drainMockHandleStatusUpdateQueue();
    });

    await waitFor(async () => {
      drainMockHandleStatusUpdateQueue();
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });

    // We return the cached data
    expect(result.current.allRepos).toEqual([
      ...repoLocationToRepos(repositoryLocation1),
      ...repoLocationToRepos(repositoryLocation2),
      ...repoLocationToRepos(repositoryLocation3),
    ]);

    expect(result.current.data).toEqual({
      [location1.name]: location1,
      [location2.name]: location2,
      [location3.name]: location3,
    });

    expect(mockCbs[0]).toHaveBeenCalled();
    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();

    await act(async () => {
      // Our mocks have a delay of 10
      jest.advanceTimersByTime(10);
      jest.runAllTicks();
      drainMockLoadFromServerQueue();
    });

    // We detect the third code location was deleted
    expect(result.current.allRepos).toEqual([
      ...repoLocationToRepos(repositoryLocation1),
      ...repoLocationToRepos(repositoryLocation2),
    ]);

    expect(result.current.data).toEqual({
      [location1.name]: location1,
      [location2.name]: location2,
    });

    // We query for the the updated cached locations
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    // We now have the latest data
    expect(result.current.data).toEqual({
      [location1.name]: updatedLocation1,
      [location2.name]: updatedLocation2,
    });
  });

  it('Handles code location load errors gracefully', async () => {
    const errorMessage = 'Failed to load code location';
    const error = buildPythonError({message: errorMessage});
    const {location1, location2, location3, caches} = getLocationMocks(0);

    // Set location2 to have an error
    location2.locationOrLoadError = error;

    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    mocks[0]!.maxUsageCount = 999;
    const mockCbs = mocks.map(getMockResultFn);

    caches.codeLocationStatusQuery.has.mockResolvedValue(false);
    caches.location1.has.mockResolvedValue(false);
    caches.location2.has.mockResolvedValue(false);
    caches.location3.has.mockResolvedValue(false);
    caches.location1Assets.has.mockResolvedValue(false);
    caches.location2Assets.has.mockResolvedValue(false);
    caches.location3Assets.has.mockResolvedValue(false);

    const {result} = renderWithMocks(mocks);

    await waitFor(() => {
      expect(result.current.loadingNonAssets).toEqual(true);
      expect(result.current.loadingAssets).toEqual(true);
    });

    // Run the code location status query
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    await waitFor(() => {
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();

      expect(mockCbs[1]).toHaveBeenCalled();
      expect(mockCbs[2]).toHaveBeenCalled();
      expect(mockCbs[3]).toHaveBeenCalled();
      expect(mockCbs[4]).toHaveBeenCalled();
      expect(mockCbs[5]).toHaveBeenCalled();
      expect(mockCbs[6]).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });

    expect(result.current.data).toEqual({
      [location1.name]: location1,
      [location2.name]: location2,
      [location3.name]: location3,
    });

    // Verify that repositories from location2 are not included
    expect(result.current.allRepos).toEqual([
      ...repoLocationToRepos(location1.locationOrLoadError as any),
      ...repoLocationToRepos(location3.locationOrLoadError as any),
    ]);
  });

  it('Handles empty code location status gracefully', async () => {
    const caches = getLocationMocks(0).caches;
    caches.codeLocationStatusQuery.has.mockResolvedValue(false);

    const mocks = buildWorkspaceMocks([], {delay: 10});
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    mocks[0]!.maxUsageCount = 9999;

    const {result} = renderWithMocks(mocks);

    await waitFor(() => {
      expect(result.current.loadingNonAssets).toEqual(true);
      expect(result.current.loadingAssets).toEqual(true);
    });

    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    await waitFor(() => {
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
  });

  it("Doesn't overfetch the same code location version on cascading location query responses", async () => {
    const {location1, location2, location3, caches} = getLocationMocks(-1);

    caches.codeLocationStatusQuery.has.mockResolvedValue(false);
    caches.location1.has.mockResolvedValue(false);

    const mocks = buildWorkspaceMocks([location1, location2, location3], {
      cascadingUpdates: true,
      maxUsageCount: 9999,
    });
    const mockCbs = mocks.map(getMockResultFn);

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const {result} = renderWithMocks([...mocks, mocks[0]!]);

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
    await waitFor(() => {
      expect(result.current.loadingNonAssets).toEqual(true);
      expect(result.current.loadingAssets).toEqual(true);
    });

    await waitFor(() => {
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });

    await waitFor(() => {
      // Ensure no additional fetches were made
      expect(mockCbs[1]).toHaveBeenCalledTimes(1);
      expect(mockCbs[2]).toHaveBeenCalledTimes(1);
      expect(mockCbs[3]).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      // Exhaust any remaining tasks so they don't affect the next test.
      await jest.runAllTicks();
    });
  });

  it('refetches code location status when refetchAll is called but doesn't refetch location queries if they are up to date', async () => {
    const {location1, location2, location3, caches} = getLocationMocks(0);
    caches.codeLocationStatusQuery.has.mockResolvedValue(false);
    caches.location1.has.mockResolvedValue(false);
    caches.location2.has.mockResolvedValue(false);
    caches.location3.has.mockResolvedValue(false);
    caches.location1Assets.has.mockResolvedValue(false);
    caches.location2Assets.has.mockResolvedValue(false);
    caches.location3Assets.has.mockResolvedValue(false);

    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});

    const mocks2 = buildWorkspaceMocks([location1, location2, location3], {delay: 10});
    const mockCbs = mocks.map(getMockResultFn);
    const mockCbs2 = mocks2.map(getMockResultFn);

    const {result} = renderWithMocks([...mocks, ...mocks2]);

    await waitFor(() => {
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });

    expect(mockCbs[0]).toHaveBeenCalledTimes(1);
    expect(mockCbs[1]).toHaveBeenCalledTimes(1);
    expect(mockCbs[2]).toHaveBeenCalledTimes(1);
    expect(mockCbs[3]).toHaveBeenCalledTimes(1);
    expect(mockCbs[4]).toHaveBeenCalledTimes(1);
    expect(mockCbs[5]).toHaveBeenCalledTimes(1);
    expect(mockCbs[6]).toHaveBeenCalledTimes(1);

    let promise: Promise<void>;
    await act(async () => {
      promise = result.current.refetch();
    });

    await waitFor(async () => {
      await expect(promise).resolves.toBeUndefined();
      expect(mockCbs2[0]).toHaveBeenCalledTimes(1);
      expect(mockCbs2[1]).not.toHaveBeenCalled();
      expect(mockCbs2[2]).not.toHaveBeenCalled();
      expect(mockCbs2[3]).not.toHaveBeenCalled();
      expect(mockCbs2[4]).not.toHaveBeenCalled();
      expect(mockCbs2[5]).not.toHaveBeenCalled();
      expect(mockCbs2[6]).not.toHaveBeenCalled();
    });

    await act(async () => {
      // Exhaust any remaining tasks so they don't affect the next test.
      await jest.runAllTicks();
    });
  });

  it('refetches code location status when refetchAll is called and refetches only locations that have changed', async () => {
    const {location1, location2, location3, caches} = getLocationMocks(0);
    caches.codeLocationStatusQuery.has.mockResolvedValue(false);
    caches.location1.has.mockResolvedValue(false);
    caches.location2.has.mockResolvedValue(false);
    caches.location3.has.mockResolvedValue(false);
    caches.location1Assets.has.mockResolvedValue(false);
    caches.location2Assets.has.mockResolvedValue(false);
    caches.location3Assets.has.mockResolvedValue(false);

    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});

    const {location3: updatedLocation3} = getLocationMocks(1);
    const mocks2 = buildWorkspaceMocks([location1, location2, updatedLocation3], {delay: 10});
    const mockCbs = mocks.map(getMockResultFn);
    const mockCbs2 = mocks2.map(getMockResultFn);

    const {result} = renderWithMocks([...mocks, ...mocks2]);

    await waitFor(() => {
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();
      expect(result.current.loadingNonAssets).toEqual(false);
      expect(result.current.loadingAssets).toEqual(false);
    });

    await waitFor(() => {
      expect(mockCbs[0]).toHaveBeenCalledTimes(1);
      expect(mockCbs[1]).toHaveBeenCalledTimes(1);
      expect(mockCbs[2]).toHaveBeenCalledTimes(1);
      expect(mockCbs[3]).toHaveBeenCalledTimes(1);
      expect(mockCbs[4]).toHaveBeenCalledTimes(1);
      expect(mockCbs[5]).toHaveBeenCalledTimes(1);
      expect(mockCbs[6]).toHaveBeenCalledTimes(1);
    });

    let promise: Promise<void>;
    await act(async () => {
      promise = result.current.refetch();
    });

    await waitFor(async () => {
      drainMockHandleStatusUpdateQueue();
      drainMockLoadFromServerQueue();
      await expect(promise).resolves.toBeUndefined();
      expect(mockCbs2[0]).toHaveBeenCalledTimes(1);
      expect(mockCbs2[1]).not.toHaveBeenCalled();
      expect(mockCbs2[2]).not.toHaveBeenCalled();
      // The third location query was updated so it was refetched immediately
      expect(mockCbs2[3]).toHaveBeenCalledTimes(1);
      expect(result.current.locationStatuses[location3.name]?.versionKey).toEqual(
        updatedLocation3.versionKey,
      );
      expect(mockCbs2[4]).not.toHaveBeenCalled();
      expect(mockCbs2[5]).not.toHaveBeenCalled();
      // The third location query was updated so it was refetched immediately
      expect(mockCbs2[6]).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      // Exhaust any remaining tasks so they don't affect the next test.
      await jest.runAllTicks();
    });
  });
});
