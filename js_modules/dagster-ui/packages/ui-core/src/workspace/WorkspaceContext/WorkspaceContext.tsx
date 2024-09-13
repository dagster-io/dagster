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

export const WorkspaceContext = React.createContext<WorkspaceState>({} as WorkspaceState);

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
      const cachedData = await loadCachedLocationData(
        localCacheIdPrefix,
        getCachedData,
        previousLocationVersionsRef,
      );
      setLocationEntryData(cachedData);
    })();
  }, [localCacheIdPrefix, getCachedData]);

  useEffect(() => {
    refreshLocationsIfNeeded(
      locationStatuses,
      locationEntryData,
      previousLocationVersionsRef.current,
      client,
      localCacheIdPrefix,
      getData,
      setLocationEntryData,
      previousLocationVersionsRef,
    );
  }, [locationStatuses, locationEntryData, client, localCacheIdPrefix, getData, loading]);

  useEffect(() => {
    if (loading) {
      return;
    }

    handleDeletedLocations(
      previousLocationVersionsRef.current,
      locationStatuses,
      clearCachedData,
      localCacheIdPrefix,
      setLocationEntryData,
      previousLocationVersionsRef,
    );
  }, [locationStatuses, clearCachedData, localCacheIdPrefix, setLocationEntryData, loading]);

  const locationEntries = useMemo(
    () => extractLocationEntries(locationEntryData),
    [locationEntryData],
  );
  const allRepos = useAllRepos(locationEntries);

  const {visibleRepos, toggleVisible, setVisible, setHidden} = useVisibleRepos(allRepos);

  const refetch = useCallback(async () => {
    const results = (
      await Promise.all(
        Object.values(locationStatuses).map(async (location) => {
          return await fetchLocationData(
            location.name,
            client,
            localCacheIdPrefix,
            getData,
            setLocationEntryData,
          );
        }),
      )
    ).filter((x) => x) as Array<LocationWorkspaceQuery>;
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

async function loadCachedLocationData(
  localCacheIdPrefix: string | undefined,
  getCachedData: ReturnType<typeof useGetCachedData>,
  previousLocationVersionsRef: React.MutableRefObject<Record<string, string>>,
) {
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

async function refreshLocationsIfNeeded(
  locationStatuses: Record<string, LocationStatusEntryFragment>,
  locationEntryData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
  previousLocationVersions: Record<string, string>,
  client: ApolloClient<any>,
  localCacheIdPrefix: string | undefined,
  getData: ReturnType<typeof useGetData>,
  setLocationEntryData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >,
  previousLocationVersionsRef: React.MutableRefObject<Record<string, string>>,
) {
  const locationsToFetch = identifyStaleLocations(
    locationStatuses,
    locationEntryData,
    previousLocationVersions,
  );

  if (locationsToFetch.length === 0) {
    return;
  }

  await Promise.all(
    locationsToFetch.map((location) =>
      fetchLocationData(location.name, client, localCacheIdPrefix, getData, setLocationEntryData),
    ),
  );

  previousLocationVersionsRef.current = mapLocationVersions(locationStatuses);
}

function handleDeletedLocations(
  previousLocationVersions: Record<string, string>,
  locationStatuses: Record<string, LocationStatusEntryFragment>,
  clearCachedData: ReturnType<typeof useClearCachedData>,
  localCacheIdPrefix: string | undefined,
  setLocationEntryData: React.Dispatch<
    React.SetStateAction<Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>>
  >,
  previousLocationVersionsRef: React.MutableRefObject<Record<string, string>>,
) {
  const removedLocations = identifyRemovedLocations(previousLocationVersions, locationStatuses);

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

  const updatedPrevVersions = {...previousLocationVersionsRef.current};
  removedLocations.forEach((name) => {
    delete updatedPrevVersions[name];
  });
  previousLocationVersionsRef.current = updatedPrevVersions;
}

async function fetchLocationData(
  name: string,
  client: ApolloClient<any>,
  localCacheIdPrefix: string | undefined,
  getData: ReturnType<typeof useGetData>,
  setLocationEntryData: React.Dispatch<
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

function identifyRemovedLocations(
  previousStatuses: Record<string, string>,
  currentStatuses: Record<string, LocationStatusEntryFragment>,
): string[] {
  return Object.keys(previousStatuses).filter((name) => !currentStatuses[name]);
}

function extractLocationEntries(
  locationEntryData: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
) {
  return Object.values(locationEntryData).filter(
    (entry): entry is WorkspaceLocationNodeFragment =>
      entry?.__typename === 'WorkspaceLocationEntry',
  );
}

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
