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
import {ApolloClient, useApolloClient} from '../../apollo-client';
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
  refetch: () => Promise<LocationWorkspaceQuery[]>;
  toggleVisible: SetVisibleOrHiddenFn;
  setVisible: SetVisibleOrHiddenFn;
  setHidden: SetVisibleOrHiddenFn;
}

export const WorkspaceContext = React.createContext<WorkspaceState>(
  new Error('WorkspaceContext should never be uninitialized') as any,
);

interface BaseLocationParams {
  localCacheIdPrefix?: string;
  getCachedData: ReturnType<typeof useGetCachedData>;
  getData: ReturnType<typeof useGetData>;
  clearCachedData: ReturnType<typeof useClearCachedData>;
  client: ApolloClient<any>;
}

interface LoadCachedLocationDataParams
  extends Pick<BaseLocationParams, 'localCacheIdPrefix' | 'getCachedData'> {
  previousLocationVersionsRef: React.MutableRefObject<Record<string, string>>;
}

interface RefreshLocationsIfNeededParams
  extends Omit<BaseLocationParams, 'getCachedData' | 'clearCachedData'> {
  locationStatuses: Record<string, LocationStatusEntryFragment>;
  locationEntryData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>;
  setLocationEntryData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >;
  previousLocationVersionsRef: React.MutableRefObject<Record<string, string>>;
}

interface HandleDeletedLocationsParams
  extends Pick<BaseLocationParams, 'localCacheIdPrefix' | 'clearCachedData'> {
  locationStatuses: Record<string, LocationStatusEntryFragment>;
  setLocationEntryData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >;
  previousLocationVersionsRef: React.MutableRefObject<Record<string, string>>;
}

interface FetchLocationDataParams
  extends Pick<BaseLocationParams, 'client' | 'localCacheIdPrefix' | 'getData'> {
  name: string;
  setLocationEntryData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >;
}

export const WorkspaceProvider = ({children}: {children: React.ReactNode}) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  const client = useApolloClient();
  const getCachedData = useGetCachedData();
  const clearCachedData = useClearCachedData();
  const getData = useGetData();

  const [locationEntryData, setLocationEntryData] = useState<
    Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>
  >({});

  const previousLocationVersionsRef = useRef<Record<string, string>>({});

  const {locationStatuses, loading: loadingLocationStatuses} =
    useCodeLocationStatuses(localCacheIdPrefix);

  const loading =
    loadingLocationStatuses ||
    !Object.keys(locationStatuses).every((locationName) => locationEntryData[locationName]);

  useLayoutEffect(() => {
    (async () => {
      const params: LoadCachedLocationDataParams = {
        localCacheIdPrefix,
        getCachedData,
        previousLocationVersionsRef,
      };
      const cachedData = await loadCachedLocationData(params);
      setLocationEntryData(cachedData);
    })();
  }, [localCacheIdPrefix, getCachedData]);

  useEffect(() => {
    const params: RefreshLocationsIfNeededParams = {
      locationStatuses,
      locationEntryData,
      client,
      localCacheIdPrefix,
      getData,
      setLocationEntryData,
      previousLocationVersionsRef,
    };
    refreshLocationsIfNeeded(params);
  }, [locationStatuses, locationEntryData, client, localCacheIdPrefix, getData, loading]);

  useEffect(() => {
    if (loading) {
      return;
    }

    const params: HandleDeletedLocationsParams = {
      locationStatuses,
      clearCachedData,
      localCacheIdPrefix,
      setLocationEntryData,
      previousLocationVersionsRef,
    };
    handleDeletedLocations(params);
  }, [locationStatuses, clearCachedData, localCacheIdPrefix, setLocationEntryData, loading]);

  const locationEntries = useMemo(
    () => extractLocationEntries(locationEntryData),
    [locationEntryData],
  );
  const allRepos = useAllRepos(locationEntries);

  const {visibleRepos, toggleVisible, setVisible, setHidden} = useVisibleRepos(allRepos);

  const refetch = useCallback(async () => {
    const promises = Object.values(locationStatuses).map(async (location) => {
      const params: FetchLocationDataParams = {
        name: location.name,
        client,
        localCacheIdPrefix,
        getData,
        setLocationEntryData,
      };
      return await fetchLocationData(params);
    });

    const results = (await Promise.all(promises)).filter((x) => x) as Array<LocationWorkspaceQuery>;
    return results;
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
        data: locationEntryData,
        refetch,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

/**
 * Loads cached location data from IndexedDB.
 */
async function loadCachedLocationData(
  params: LoadCachedLocationDataParams,
): Promise<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>> {
  const {localCacheIdPrefix, getCachedData, previousLocationVersionsRef} = params;
  const cachedData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment> = {};
  const cachedStatusData = await getCachedData<CodeLocationStatusQuery>({
    key: `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`,
    version: CodeLocationStatusQueryVersion,
  });
  const cachedLocations = extractLocationStatuses(cachedStatusData);

  await Promise.all(
    Object.values(cachedLocations).map(async (location) => {
      const locationData = await getCachedData<LocationWorkspaceQuery>({
        key: `${localCacheIdPrefix}${locationWorkspaceKey(location.name)}`,
        version: LocationWorkspaceQueryVersion,
      });
      const entry = locationData?.workspaceLocationEntryOrError;
      if (entry) {
        cachedData[location.name] = entry;
      }
    }),
  );

  previousLocationVersionsRef.current = mapLocationVersions(cachedLocations);
  return cachedData;
}

/**
 * Refreshes locations if they are stale based on versioning.
 */
async function refreshLocationsIfNeeded(params: RefreshLocationsIfNeededParams): Promise<void> {
  const {
    locationStatuses,
    locationEntryData,
    client,
    localCacheIdPrefix,
    getData,
    setLocationEntryData,
    previousLocationVersionsRef,
  } = params;

  const locationsToFetch = identifyStaleLocations(
    locationStatuses,
    locationEntryData,
    previousLocationVersionsRef.current,
  );

  if (locationsToFetch.length === 0) {
    return;
  }

  await Promise.all(
    locationsToFetch.map((location) =>
      fetchLocationData({
        name: location.name,
        client,
        localCacheIdPrefix,
        getData,
        setLocationEntryData,
      }),
    ),
  );

  previousLocationVersionsRef.current = mapLocationVersions(locationStatuses);
}

/**
 * Handles the cleanup of deleted locations by removing them from the cache and state.
 */
function handleDeletedLocations(params: HandleDeletedLocationsParams): void {
  const {
    locationStatuses,
    clearCachedData,
    localCacheIdPrefix,
    setLocationEntryData,
    previousLocationVersionsRef,
  } = params;

  const removedLocations = identifyRemovedLocations(
    previousLocationVersionsRef.current,
    locationStatuses,
  );

  if (removedLocations.length === 0) {
    return;
  }

  removedLocations.forEach((name) => {
    clearCachedData({
      key: `${localCacheIdPrefix}${locationWorkspaceKey(name)}`,
    });
  });

  setLocationEntryData((prevData) => {
    const updatedData = {...prevData};
    removedLocations.forEach((name) => {
      delete updatedData[name];
    });
    return updatedData;
  });

  previousLocationVersionsRef.current = mapLocationVersions(locationStatuses);
}

/**
 * Fetches data for a specific location.
 */
async function fetchLocationData(
  params: FetchLocationDataParams,
): Promise<LocationWorkspaceQuery | undefined> {
  const {name, client, localCacheIdPrefix, getData, setLocationEntryData} = params;
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
      setLocationEntryData((prevData) => ({
        ...prevData,
        [name]: entry,
      }));
    }
    return data;
  } catch (error) {
    console.error(`Error fetching location data for ${name}:`, error);
  }
  return undefined;
}

/**
 * Extracts location statuses from the provided query data.
 *
 * @param data - The result of the CodeLocationStatusQuery.
 * @returns A record mapping location names to their status entries.
 */
function extractLocationStatuses(
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

/**
 * Maps location statuses to their corresponding version keys.
 *
 * @param locationStatuses - A record of location statuses.
 * @returns A record mapping location names to their version keys.
 */
function mapLocationVersions(
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

/**
 * Identifies locations that are stale and need to be refreshed.
 *
 * @param locationStatuses - Current location statuses.
 * @param locationEntryData - Current location entry data.
 * @param previousLocationVersions - Previously recorded location versions.
 * @returns An array of location status entries that are stale.
 */
function identifyStaleLocations(
  locationStatuses: Record<string, LocationStatusEntryFragment>,
  locationEntryData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
  previousLocationVersions: Record<string, string>,
): LocationStatusEntryFragment[] {
  return Object.values(locationStatuses).filter((statusEntry) => {
    const prevVersion = previousLocationVersions[statusEntry.name];
    const currentVersion = statusEntry.versionKey || '';
    const entry = locationEntryData[statusEntry.name];
    const locationEntry = entry?.__typename === 'WorkspaceLocationEntry' ? entry : null;
    const dataVersion = locationEntry?.versionKey || '';
    return currentVersion !== prevVersion || currentVersion !== dataVersion;
  });
}

/**
 * Identifies locations that have been removed from the current statuses.
 *
 * @param previousStatuses - Previously recorded location versions.
 * @param currentStatuses - Current location statuses.
 * @returns An array of location names that have been removed.
 */
function identifyRemovedLocations(
  previousStatuses: Record<string, string>,
  currentStatuses: Record<string, LocationStatusEntryFragment>,
): string[] {
  return Object.keys(previousStatuses).filter((name) => !currentStatuses[name]);
}

/**
 * Extracts location entries from the provided location entry data.
 *
 * @param locationEntryData - A record of location entry data.
 * @returns An array of workspace location node fragments.
 */
function extractLocationEntries(
  locationEntryData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
): WorkspaceRepositoryLocationNode[] {
  return Object.values(locationEntryData).filter(
    (entry): entry is WorkspaceLocationNodeFragment =>
      entry?.__typename === 'WorkspaceLocationEntry',
  );
}

/**
 * Retrieves and sorts all repositories from the provided location entries.
 *
 * @param locationEntries - An array of workspace repository location nodes.
 * @returns A sorted array of Dagster repository options.
 */
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

/**
 * Custom hook to retrieve code location statuses using IndexedDB caching.
 *
 * @param localCacheIdPrefix - Optional prefix for cache keys.
 * @returns An object containing location statuses and loading state.
 */
function useCodeLocationStatuses(localCacheIdPrefix: string | undefined) {
  const {data: codeLocationStatusData, fetch} = useIndexedDBCachedQuery<
    CodeLocationStatusQuery,
    CodeLocationStatusQueryVariables
  >({
    query: CODE_LOCATION_STATUS_QUERY,
    version: CodeLocationStatusQueryVersion,
    key: `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`,
  });

  if (typeof jest === 'undefined') {
    // Only do this outside of jest for now so that we don't need to add RecoilRoot around everything...
    // we will switch to jotai at some point instead... which doesnt require a
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const setCodeLocationStatusAtom = useSetRecoilState(codeLocationStatusAtom);

    // eslint-disable-next-line react-hooks/rules-of-hooks
    useLayoutEffect(() => {
      if (codeLocationStatusData) {
        setCodeLocationStatusAtom(codeLocationStatusData);
      }
    }, [codeLocationStatusData, setCodeLocationStatusAtom]);
  }

  const refresh = useCallback(async () => {
    await fetch();
  }, [fetch]);

  useRefreshAtInterval({
    refresh,
    intervalMs: 5000,
    leading: true,
  });

  const locationStatuses = useMemo(
    () => extractLocationStatuses(codeLocationStatusData),
    [codeLocationStatusData],
  );

  return {locationStatuses, loading: !codeLocationStatusData};
}
