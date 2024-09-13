import sortBy from 'lodash/sortBy';
import React, {
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {useSetRecoilState} from 'recoil';

import {CODE_LOCATION_STATUS_QUERY, LOCATION_WORKSPACE_QUERY} from './WorkspaceQueries';
import {
  CodeLocationStatusQuery,
  CodeLocationStatusQueryVariables,
  CodeLocationStatusQueryVersion,
  LocationStatusEntryFragment,
  LocationWorkspaceQuery,
  LocationWorkspaceQueryVariables,
  LocationWorkspaceQueryVersion,
  WorkspaceLocationNodeFragment,
  WorkspaceScheduleFragment,
  WorkspaceSensorFragment,
} from './types/WorkspaceQueries.types';
import {
  DagsterRepoOption,
  SetVisibleOrHiddenFn,
  locationWorkspaceKey,
  repoLocationToRepos,
  useVisibleRepos,
} from './util';
import {useApolloClient} from '../../apollo-client';
import {AppContext} from '../../app/AppContext';
import {useRefreshAtInterval} from '../../app/QueryRefresh';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {codeLocationStatusAtom} from '../../nav/useCodeLocationsStatus';
import {
  useClearCachedData,
  useGetCachedData,
  useGetData,
  useIndexedDBCachedQuery,
} from '../../search/useIndexedDBCachedQuery';

export const CODE_LOCATION_STATUS_QUERY_KEY = '/CodeLocationStatusQuery';
export const HIDDEN_REPO_KEYS = 'dagster.hidden-repo-keys';

export type WorkspaceRepositorySensor = WorkspaceSensorFragment;
export type WorkspaceRepositorySchedule = WorkspaceScheduleFragment;
export type WorkspaceRepositoryLocationNode = WorkspaceLocationNodeFragment;

interface WorkspaceState {
  loading: boolean;
  locationEntries: WorkspaceRepositoryLocationNode[];
  locationStatuses: Record<string, LocationStatusEntryFragment>;
  allRepos: DagsterRepoOption[];
  visibleRepos: DagsterRepoOption[];
  data: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>;
  refetch: () => Promise<void>;
  toggleVisible: SetVisibleOrHiddenFn;
  setVisible: SetVisibleOrHiddenFn;
  setHidden: SetVisibleOrHiddenFn;
}

export const WorkspaceContext = React.createContext<WorkspaceState>({} as WorkspaceState);

export const WorkspaceProvider = ({children}: {children: React.ReactNode}) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  const client = useApolloClient();
  const setCodeLocationStatusAtom = useSetRecoilState(codeLocationStatusAtom);
  const getCachedData = useGetCachedData();
  const clearCachedData = useClearCachedData();
  const getData = useGetData();

  // State for location entries data
  const [locationEntriesData, setLocationEntriesData] = useState<
    Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>
  >({});

  // Use useRef to store previous location versions
  const prevLocationVersionsRef = useRef<Record<string, string>>({});

  // Fetch and manage code location statuses
  const {locationStatuses, loading: loadingStatusData} = useCodeLocationStatuses(
    localCacheIdPrefix,
    setCodeLocationStatusAtom,
  );

  const loading =
    loadingStatusData ||
    !Object.keys(locationStatuses).every((locationName) => locationEntriesData[locationName]);

  // Load initial data from cache
  useLayoutEffect(() => {
    (async () => {
      const allData = await loadInitialDataFromCache(
        localCacheIdPrefix,
        getCachedData,
        prevLocationVersionsRef,
      );
      setLocationEntriesData(allData);
    })();
  }, [localCacheIdPrefix, getCachedData]);

  useEffect(() => {
    refetchLocationsIfNeeded(
      locationStatuses,
      locationEntriesData,
      prevLocationVersionsRef.current,
      client,
      localCacheIdPrefix,
      getData,
      setLocationEntriesData,
      prevLocationVersionsRef,
    );
  }, [locationStatuses, locationEntriesData, client, localCacheIdPrefix, getData, loading]);

  useEffect(() => {
    if (loading) {
      return;
    }

    handleRemovedLocations(
      prevLocationVersionsRef.current,
      locationStatuses,
      clearCachedData,
      localCacheIdPrefix,
      setLocationEntriesData,
      prevLocationVersionsRef,
    );
  }, [locationStatuses, clearCachedData, localCacheIdPrefix, setLocationEntriesData, loading]);

  // Compute location entries and all repositories
  const locationEntries = useLocationEntries(locationEntriesData);
  const allRepos = useAllRepos(locationEntries);

  // Manage repository visibility
  const {visibleRepos, toggleVisible, setVisible, setHidden} = useVisibleRepos(allRepos);

  // Provide refetch function
  const refetchAllLocations = useCallback(async () => {
    await Promise.all(
      Object.values(locationStatuses).map(async (location) => {
        await refetchLocation(
          location.name,
          client,
          localCacheIdPrefix,
          getData,
          setLocationEntriesData,
        );
      }),
    );
  }, [locationStatuses, client, localCacheIdPrefix, getData]);

  return (
    <WorkspaceContext.Provider
      value={{
        loading,
        locationEntries,
        locationStatuses,
        allRepos,
        visibleRepos,
        toggleVisible,
        setVisible,
        setHidden,
        data: locationEntriesData,
        refetch: refetchAllLocations,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

// Custom hook to fetch and manage code location statuses
function useCodeLocationStatuses(
  localCacheIdPrefix: string | undefined,
  setCodeLocationStatusAtom: any,
) {
  const {data: codeLocationStatusData, fetch} = useIndexedDBCachedQuery<
    CodeLocationStatusQuery,
    CodeLocationStatusQueryVariables
  >({
    query: CODE_LOCATION_STATUS_QUERY,
    version: CodeLocationStatusQueryVersion,
    key: `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`,
  });

  useEffect(() => {
    if (codeLocationStatusData) {
      setCodeLocationStatusAtom(codeLocationStatusData);
    }
  }, [codeLocationStatusData, setCodeLocationStatusAtom]);

  useEffect(() => {
    // Cleanup old cache
    indexedDB.deleteDatabase('indexdbQueryCache:RootWorkspace');
  }, []);

  const refresh = useCallback(async () => {
    await fetch();
  }, [fetch]);

  useRefreshAtInterval({
    refresh,
    intervalMs: 5000,
    leading: true,
  });

  const locationStatuses = useMemo(
    () => extractLocations(codeLocationStatusData),
    [codeLocationStatusData],
  );

  return {locationStatuses, loading: !codeLocationStatusData};
}

// Function to load initial data from cache
async function loadInitialDataFromCache(
  localCacheIdPrefix: string | undefined,
  getCachedData: ReturnType<typeof useGetCachedData>,
  prevLocationVersionsRef: React.MutableRefObject<Record<string, string>>,
) {
  const allData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment> = {};
  const cachedStatusData = await getCachedData<CodeLocationStatusQuery>({
    key: `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`,
    version: CodeLocationStatusQueryVersion,
  });
  const cachedLocations = extractLocations(cachedStatusData);

  await Promise.all(
    Object.values(cachedLocations).map(async (location) => {
      const locationData = await getCachedData<LocationWorkspaceQuery>({
        key: `${localCacheIdPrefix}${locationWorkspaceKey(location.name)}`,
        version: LocationWorkspaceQueryVersion,
      });
      const entry = locationData?.workspaceLocationEntryOrError;
      if (entry) {
        allData[location.name] = entry;
      }
    }),
  );

  prevLocationVersionsRef.current = getLocationVersionMap(cachedLocations);
  return allData;
}

// Function to refetch locations if needed
async function refetchLocationsIfNeeded(
  locationStatuses: Record<string, LocationStatusEntryFragment>,
  locationEntriesData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
  prevLocationVersions: Record<string, string>,
  client: any,
  localCacheIdPrefix: string | undefined,
  getData: ReturnType<typeof useGetData>,
  setLocationEntriesData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >,
  prevLocationVersionsRef: React.MutableRefObject<Record<string, string>>,
) {
  const locationsToFetch = getLocationsToFetch(
    locationStatuses,
    locationEntriesData,
    prevLocationVersions,
  );

  if (locationsToFetch.length === 0) {
    return;
  }

  await Promise.all(
    locationsToFetch.map((location) =>
      refetchLocation(location.name, client, localCacheIdPrefix, getData, setLocationEntriesData),
    ),
  );

  prevLocationVersionsRef.current = getLocationVersionMap(locationStatuses);
}

// Function to handle removed locations
function handleRemovedLocations(
  prevLocationVersions: Record<string, string>,
  locationStatuses: Record<string, LocationStatusEntryFragment>,
  clearCachedData: ReturnType<typeof useClearCachedData>,
  localCacheIdPrefix: string | undefined,
  setLocationEntriesData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >,
  prevLocationVersionsRef: React.MutableRefObject<Record<string, string>>,
) {
  const removedLocations = getRemovedLocations(prevLocationVersions, locationStatuses);

  if (removedLocations.length === 0) {
    return;
  }

  removedLocations.forEach((name) => {
    clearCachedData({
      key: `${localCacheIdPrefix}${locationWorkspaceKey(name)}`,
    });
  });

  setLocationEntriesData((prevData) => {
    const updatedData = {...prevData};
    removedLocations.forEach((name) => {
      delete updatedData[name];
    });
    return updatedData;
  });

  // Update prevLocationVersionsRef to reflect removed locations
  const updatedPrevVersions = {...prevLocationVersionsRef.current};
  removedLocations.forEach((name) => {
    delete updatedPrevVersions[name];
  });
  prevLocationVersionsRef.current = updatedPrevVersions;
}

// Function to refetch a single location
async function refetchLocation(
  name: string,
  client: any,
  localCacheIdPrefix: string | undefined,
  getData: ReturnType<typeof useGetData>,
  setLocationEntriesData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >,
) {
  try {
    const {data} = await getData<LocationWorkspaceQuery, LocationWorkspaceQueryVariables>({
      client,
      query: LOCATION_WORKSPACE_QUERY,
      key: `${localCacheIdPrefix}${locationWorkspaceKey(name)}`,
      version: LocationWorkspaceQueryVersion,
      variables: {name},
      bypassCache: true,
    });

    const entry = data?.workspaceLocationEntryOrError;
    if (entry) {
      setLocationEntriesData((prevData) => ({
        ...prevData,
        [name]: entry,
      }));
    }
  } catch (error) {
    console.error(`Error refetching location ${name}:`, error);
  }
}

// Helper to extract locations from query data
function extractLocations(
  data: CodeLocationStatusQuery | undefined | null,
): Record<string, LocationStatusEntryFragment> {
  if (data?.locationStatusesOrError?.__typename !== 'WorkspaceLocationStatusEntries') {
    return {};
  }
  return data.locationStatusesOrError.entries.reduce(
    (acc, loc) => {
      acc[loc.name] = loc;
      return acc;
    },
    {} as Record<string, LocationStatusEntryFragment>,
  );
}

// Helper to get a map of location names to their version keys
function getLocationVersionMap(
  locationStatuses: Record<string, LocationStatusEntryFragment>,
): Record<string, string> {
  return Object.entries(locationStatuses).reduce(
    (acc, [name, status]) => {
      acc[name] = status.versionKey || '';
      return acc;
    },
    {} as Record<string, string>,
  );
}

// Helper to determine locations that need refetching
function getLocationsToFetch(
  locationStatuses: Record<string, LocationStatusEntryFragment>,
  locationEntriesData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
  prevLocationVersions: Record<string, string>,
): LocationStatusEntryFragment[] {
  return Object.values(locationStatuses).filter((statusEntry) => {
    const prevVersion = prevLocationVersions[statusEntry.name];
    const currentVersion = statusEntry.versionKey || '';
    const entry = locationEntriesData[statusEntry.name];
    const locationEntry = entry?.__typename === 'WorkspaceLocationEntry' ? entry : null;
    const dataVersion = locationEntry?.versionKey || '';
    return currentVersion !== prevVersion || currentVersion !== dataVersion;
  });
}

// Helper to get removed locations
function getRemovedLocations(
  prevStatuses: Record<string, string>,
  currentStatuses: Record<string, LocationStatusEntryFragment>,
): string[] {
  return Object.keys(prevStatuses).filter((name) => !currentStatuses[name]);
}

// Custom hook to compute location entries
function useLocationEntries(
  locationEntriesData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
) {
  return useMemo(
    () =>
      Object.values(locationEntriesData).filter(
        (entry): entry is WorkspaceLocationNodeFragment =>
          entry?.__typename === 'WorkspaceLocationEntry',
      ),
    [locationEntriesData],
  );
}

// Custom hook to compute all repositories
function useAllRepos(locationEntries: WorkspaceRepositoryLocationNode[]) {
  return useMemo(() => {
    const repos = locationEntries.reduce((accum, locationEntry) => {
      if (locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
        return accum;
      }
      const repositoryLocation = locationEntry.locationOrLoadError;
      accum.push(...repoLocationToRepos(repositoryLocation));
      return accum;
    }, [] as DagsterRepoOption[]);

    return sortBy(repos, (r) => `${r.repositoryLocation.name}:${r.repository.name}`);
  }, [locationEntries]);
}
