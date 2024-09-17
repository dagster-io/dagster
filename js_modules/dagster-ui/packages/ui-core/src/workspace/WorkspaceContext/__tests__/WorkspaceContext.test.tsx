jest.useFakeTimers();

import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, renderHook, waitFor} from '@testing-library/react';
import {cache} from 'idb-lru-cache';
import {useContext} from 'react';
import {RecoilRoot} from 'recoil';

import {AppContext} from '../../../app/AppContext';
import {
  buildPythonError,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../../graphql/types';
import {
  IndexedDBCacheContext,
  KEY_PREFIX,
  createIndexedDBCacheContextValue,
} from '../../../search/useIndexedDBCachedQuery';
import {getMockResultFn} from '../../../testing/mocking';
import {
  CODE_LOCATION_STATUS_QUERY_KEY,
  WorkspaceContext,
  WorkspaceProvider,
} from '../WorkspaceContext';
import {buildWorkspaceMocks} from '../__fixtures__/Workspace.fixtures';
import {
  CodeLocationStatusQueryVersion,
  LocationWorkspaceQueryVersion,
} from '../types/WorkspaceQueries.types';
import {locationWorkspaceKey, repoLocationToRepos} from '../util';

const mockCache = cache as any;

const mockedCacheStore: Record<string, any> = {};

jest.mock('idb-lru-cache', () => {
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

afterEach(async () => {
  jest.resetModules();
  jest.clearAllMocks();
  jest.clearAllTimers();
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
            <IndexedDBCacheContext.Provider value={createIndexedDBCacheContextValue()}>
              <MockedProvider mocks={mocks}>
                <WorkspaceProvider>{children}</WorkspaceProvider>
              </MockedProvider>
            </IndexedDBCacheContext.Provider>
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
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${locationWorkspaceKey('location1')}`,
      }),
      location2: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${locationWorkspaceKey('location2')}`,
      }),
      location3: mockCache({
        dbName: `${KEY_PREFIX}${LOCAL_CACHE_ID_PREFIX}${locationWorkspaceKey('location3')}`,
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
    const mocks = buildWorkspaceMocks([location1, location2, location3], {delay: 10});
    const mockCbs = mocks.map(getMockResultFn);

    // Include code location status mock a second time since we call runOnlyPendingTimersAsync twice
    const {result} = renderWithMocks([...mocks, mocks[0]!]);

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
    expect(result.current.loading).toEqual(true);

    // Runs the code location status query
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    // First mock is the code location status query
    expect(mockCbs[0]).toHaveBeenCalled();
    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();
    expect(mockCbs[3]).not.toHaveBeenCalled();

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
    expect(result.current.loading).toEqual(true);

    // Runs the individual location queries
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    expect(mockCbs[1]).toHaveBeenCalled();
    expect(mockCbs[2]).toHaveBeenCalled();
    expect(mockCbs[3]).toHaveBeenCalled();

    await waitFor(() => {
      expect(result.current.loading).toEqual(false);
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
      value: {data: (mocks[0]! as any).result.data, version: CodeLocationStatusQueryVersion},
    });
    caches.location1.has.mockResolvedValue(true);
    caches.location1.get.mockResolvedValue({
      value: {data: (mocks[1]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location2.has.mockResolvedValue(true);
    caches.location2.get.mockResolvedValue({
      value: {data: (mocks[2]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location3.has.mockResolvedValue(true);
    caches.location3.get.mockResolvedValue({
      value: {data: (mocks[3]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });

    const mockCbs = mocks.map(getMockResultFn);

    const {result} = renderWithMocks([...mocks]);

    // await act(async () => {
    //   await jest.runOnlyPendingTimersAsync();
    // });

    await waitFor(async () => {
      expect(result.current.loading).toEqual(false);
    });
    // We queries for code location statuses but saw we were up to date
    // so we didn't call any the location queries
    expect(mockCbs[0]).toHaveBeenCalled();

    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();
    expect(mockCbs[3]).not.toHaveBeenCalled();
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
      value: {data: (mocks[0]! as any).result.data, version: CodeLocationStatusQueryVersion},
    });
    caches.location1.has.mockResolvedValue(true);
    caches.location1.get.mockResolvedValue({
      value: {data: (mocks[1]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location2.has.mockResolvedValue(true);
    caches.location2.get.mockResolvedValue({
      value: {data: (mocks[2]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location3.has.mockResolvedValue(true);
    caches.location3.get.mockResolvedValue({
      value: {data: (mocks[3]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    const mockCbs = updatedMocks.map(getMockResultFn);

    const {result} = renderWithMocks([...updatedMocks, updatedMocks[0]!]);

    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });
    // We queries for code location statuses and we see we are not up to date yet so the current data is still equal to the cached data
    expect(mockCbs[0]).toHaveBeenCalled();
    expect(mockCbs[1]).not.toHaveBeenCalled();
    expect(mockCbs[2]).not.toHaveBeenCalled();
    expect(mockCbs[3]).not.toHaveBeenCalled();

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
      await jest.runOnlyPendingTimersAsync();
    });

    expect(result.current.data).toEqual({
      [location1.name]: updatedLocation1,
      [location2.name]: updatedLocation2,
      [location3.name]: updatedLocation3,
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
      value: {data: (mocks[0]! as any).result.data, version: CodeLocationStatusQueryVersion},
    });
    caches.location1.has.mockResolvedValue(true);
    caches.location1.get.mockResolvedValue({
      value: {data: (mocks[1]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location2.has.mockResolvedValue(true);
    caches.location2.get.mockResolvedValue({
      value: {data: (mocks[2]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    caches.location3.has.mockResolvedValue(true);
    caches.location3.get.mockResolvedValue({
      value: {data: (mocks[3]! as any).result.data, version: LocationWorkspaceQueryVersion},
    });
    const mockCbs = updatedMocks.map(getMockResultFn);

    const {result} = renderWithMocks([...updatedMocks, updatedMocks[0]!]);

    await act(async () => {
      await jest.runAllTicks();
    });

    await waitFor(async () => {
      expect(result.current.loading).toEqual(false);
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
    const mockCbs = mocks.map(getMockResultFn);

    caches.codeLocationStatusQuery.has.mockResolvedValue(false);
    caches.location1.has.mockResolvedValue(false);
    caches.location2.has.mockResolvedValue(false);
    caches.location3.has.mockResolvedValue(false);

    const {result} = renderWithMocks(mocks);

    expect(result.current.loading).toEqual(true);

    // Run the code location status query
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    // Run the individual location queries
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    expect(mockCbs[1]).toHaveBeenCalled();
    expect(mockCbs[2]).toHaveBeenCalled();
    expect(mockCbs[3]).toHaveBeenCalled();

    await waitFor(() => {
      expect(result.current.loading).toEqual(false);
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

    const {result} = renderWithMocks(mocks);

    // Initial load
    await act(async () => {
      await jest.runOnlyPendingTimersAsync();
    });

    await waitFor(() => {
      expect(result.current.loading).toEqual(false);
    });

    expect(result.current.allRepos).toEqual([]);
    expect(result.current.data).toEqual({});
  });
});
