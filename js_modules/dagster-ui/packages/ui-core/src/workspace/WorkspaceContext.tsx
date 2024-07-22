import {useApolloClient} from '@apollo/client';
import sortBy from 'lodash/sortBy';
import React, {useCallback, useContext, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {useSetRecoilState} from 'recoil';

import {CODE_LOCATION_STATUS_QUERY, LOCATION_WORKSPACE_QUERY} from './WorkspaceQueries';
import {buildRepoAddress} from './buildRepoAddress';
import {findRepoContainingPipeline} from './findRepoContainingPipeline';
import {RepoAddress} from './types';
import {
  CodeLocationStatusQuery,
  CodeLocationStatusQueryVariables,
  LocationWorkspaceQuery,
  LocationWorkspaceQueryVariables,
  WorkspaceLocationFragment,
  WorkspaceLocationNodeFragment,
  WorkspaceRepositoryFragment,
  WorkspaceScheduleFragment,
  WorkspaceSensorFragment,
} from './types/WorkspaceQueries.types';
import {AppContext} from '../app/AppContext';
import {useRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {PipelineSelector} from '../graphql/types';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {codeLocationStatusAtom} from '../nav/useCodeLocationsStatus';
import {
  useClearCachedData,
  useGetCachedData,
  useGetData,
  useIndexedDBCachedQuery,
} from '../search/useIndexedDBCachedQuery';

export const CODE_LOCATION_STATUS_QUERY_KEY = '/CodeLocationStatusQuery';
export const CODE_LOCATION_STATUS_QUERY_VERSION = 1;
export const LOCATION_WORKSPACE_QUERY_VERSION = 3;
type Repository = WorkspaceRepositoryFragment;
type RepositoryLocation = WorkspaceLocationFragment;

export type WorkspaceRepositorySensor = WorkspaceSensorFragment;
export type WorkspaceRepositorySchedule = WorkspaceScheduleFragment;
export type WorkspaceRepositoryLocationNode = WorkspaceLocationNodeFragment;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

type SetVisibleOrHiddenFn = (repoAddresses: RepoAddress[]) => void;

type WorkspaceState = {
  loading: boolean;
  locationEntries: WorkspaceRepositoryLocationNode[];
  allRepos: DagsterRepoOption[];
  visibleRepos: DagsterRepoOption[];
  data: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>;
  refetch: () => Promise<LocationWorkspaceQuery[]>;

  toggleVisible: SetVisibleOrHiddenFn;
  setVisible: SetVisibleOrHiddenFn;
  setHidden: SetVisibleOrHiddenFn;
};

export const WorkspaceContext = React.createContext<WorkspaceState>(
  new Error('WorkspaceContext should never be uninitialized') as any,
);

export const HIDDEN_REPO_KEYS = 'dagster.hidden-repo-keys';

export const WorkspaceProvider = ({children}: {children: React.ReactNode}) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  const codeLocationStatusQueryResult = useIndexedDBCachedQuery<
    CodeLocationStatusQuery,
    CodeLocationStatusQueryVariables
  >({
    query: CODE_LOCATION_STATUS_QUERY,
    version: CODE_LOCATION_STATUS_QUERY_VERSION,
    key: `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`,
  });
  if (typeof jest === 'undefined') {
    // Only do this outside of jest for now so that we don't need to add RecoilRoot around everything...
    // we will switch to jotai at some point instead... which doesnt require a
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const setCodeLocationStatusAtom = useSetRecoilState(codeLocationStatusAtom);
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useLayoutEffect(() => {
      if (codeLocationStatusQueryResult.data) {
        setCodeLocationStatusAtom(codeLocationStatusQueryResult.data);
      }
    }, [codeLocationStatusQueryResult.data, setCodeLocationStatusAtom]);
  }
  indexedDB.deleteDatabase('indexdbQueryCache:RootWorkspace');

  const fetch = codeLocationStatusQueryResult.fetch;
  useRefreshAtInterval({
    refresh: useCallback(async () => {
      return await fetch();
    }, [fetch]),
    intervalMs: 5000,
    leading: true,
  });

  const {data: codeLocationStatusData} = codeLocationStatusQueryResult;

  const locationStatuses = useMemo(
    () => getLocations(codeLocationStatusData),
    [codeLocationStatusData],
  );
  const prevLocationStatuses = useRef<typeof locationStatuses>({});

  const didInitiateFetchFromCache = useRef(false);
  const [didLoadStatusData, setDidLoadStatusData] = useState(false);

  const [locationEntriesData, setLocationEntriesData] = React.useState<
    Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>
  >({});

  const getCachedData = useGetCachedData();
  const getData = useGetData();
  const clearCachedData = useClearCachedData();

  useLayoutEffect(() => {
    // Load data from the cache
    if (didInitiateFetchFromCache.current) {
      return;
    }
    didInitiateFetchFromCache.current = true;
    const allData: typeof locationEntriesData = {};
    new Promise(async (res) => {
      /**
       * 1. Load the cached code location status query
       * 2. Load the cached data for those locations
       * 3. Set the cached data to `locationsData` state
       * 4. Set prevLocations equal to these cached locations so that we can check if they
       *  have changed after the next call to codeLocationStatusQuery
       * 5. set didLoadCachedData to true to unblock the `locationsToFetch` memo so that it can compare
       *  the latest codeLocationStatusQuery result to what was in the cache.
       */
      const data = await getCachedData<CodeLocationStatusQuery>({
        key: `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`,
        version: CODE_LOCATION_STATUS_QUERY_VERSION,
      });
      const cachedLocations = getLocations(data);
      const prevCachedLocations: typeof locationStatuses = {};

      await Promise.all([
        ...Object.values(cachedLocations).map(async (location) => {
          const locationData = await getCachedData<LocationWorkspaceQuery>({
            key: `${localCacheIdPrefix}${locationWorkspaceKey(location.name)}`,
            version: LOCATION_WORKSPACE_QUERY_VERSION,
          });
          const entry = locationData?.workspaceLocationEntryOrError;
          if (!entry) {
            return;
          }
          allData[location.name] = entry;

          if (entry.__typename === 'WorkspaceLocationEntry') {
            prevCachedLocations[location.name] = location;
          }
        }),
      ]);
      prevLocationStatuses.current = prevCachedLocations;
      res(void 0);
    }).then(() => {
      setDidLoadStatusData(true);
      setLocationEntriesData(allData);
    });
  }, [getCachedData, localCacheIdPrefix, locationStatuses]);

  const client = useApolloClient();

  const refetchLocation = useCallback(
    async (name: string) => {
      const locationData = await getData<LocationWorkspaceQuery, LocationWorkspaceQueryVariables>({
        client,
        query: LOCATION_WORKSPACE_QUERY,
        key: `${localCacheIdPrefix}${locationWorkspaceKey(name)}`,
        version: LOCATION_WORKSPACE_QUERY_VERSION,
        variables: {
          name,
        },
        bypassCache: true,
      });
      const entry = locationData.data?.workspaceLocationEntryOrError;
      if (entry) {
        setLocationEntriesData((locationsData) =>
          Object.assign({}, locationsData, {
            [name]: entry,
          }),
        );
      }
      return locationData;
    },
    [client, getData, localCacheIdPrefix],
  );

  const [isRefetching, setIsRefetching] = useState(false);

  const locationsToFetch = useMemo(() => {
    if (!didLoadStatusData) {
      return [];
    }
    if (isRefetching) {
      return [];
    }
    const toFetch = Object.values(locationStatuses).filter((loc) => {
      const prev = prevLocationStatuses.current?.[loc.name];
      const d = locationEntriesData[loc.name];
      const entry = d?.__typename === 'WorkspaceLocationEntry' ? d : null;
      return (
        prev?.updateTimestamp !== loc.updateTimestamp ||
        prev?.loadStatus !== loc.loadStatus ||
        entry?.loadStatus !== loc.loadStatus
      );
    });
    prevLocationStatuses.current = locationStatuses;
    return toFetch;
  }, [didLoadStatusData, isRefetching, locationStatuses, locationEntriesData]);

  useLayoutEffect(() => {
    if (!locationsToFetch.length) {
      return;
    }
    setIsRefetching(true);
    Promise.all(
      locationsToFetch.map(async (location) => {
        return await refetchLocation(location.name);
      }),
    ).then(() => {
      setIsRefetching(false);
    });
  }, [refetchLocation, locationsToFetch]);

  const locationsRemoved = useMemo(
    () =>
      Array.from(
        new Set([
          ...Object.values(prevLocationStatuses.current).filter(
            (loc) => loc && !locationStatuses[loc.name],
          ),
          ...Object.values(locationEntriesData).filter(
            (loc): loc is WorkspaceLocationNodeFragment =>
              loc && loc?.__typename === 'WorkspaceLocationEntry' && !locationStatuses[loc.name],
          ),
        ]),
      ),
    [locationStatuses, locationEntriesData],
  );

  useLayoutEffect(() => {
    if (!locationsRemoved.length) {
      return;
    }
    const copy = {...locationEntriesData};
    locationsRemoved.forEach((loc) => {
      delete copy[loc.name];
      clearCachedData({key: `${localCacheIdPrefix}${locationWorkspaceKey(loc.name)}`});
    });
    if (Object.keys(copy).length !== Object.keys(locationEntriesData).length) {
      setLocationEntriesData(copy);
    }
  }, [clearCachedData, localCacheIdPrefix, locationEntriesData, locationsRemoved]);

  const locationEntries = useMemo(
    () =>
      Object.values(locationEntriesData).filter(
        (entry): entry is WorkspaceLocationNodeFragment =>
          !!entry && entry.__typename === 'WorkspaceLocationEntry',
      ),
    [locationEntriesData],
  );

  const allRepos = React.useMemo(() => {
    let allRepos: DagsterRepoOption[] = [];

    allRepos = sortBy(
      locationEntries.reduce((accum, locationEntry) => {
        if (locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
          return accum;
        }
        const repositoryLocation = locationEntry.locationOrLoadError;
        const reposForLocation = repoLocationToRepos(repositoryLocation);
        accum.push(...reposForLocation);
        return accum;
      }, [] as DagsterRepoOption[]),

      // Sort by repo location, then by repo
      (r) => `${r.repositoryLocation.name}:${r.repository.name}`,
    );

    return allRepos;
  }, [locationEntries]);

  const {visibleRepos, toggleVisible, setVisible, setHidden} = useVisibleRepos(allRepos);

  const locationsRef = useUpdatingRef(locationStatuses);

  const refetch = useCallback(async () => {
    return await Promise.all(
      Object.values(locationsRef.current).map(async (location) => {
        const result = await refetchLocation(location.name);
        return result.data;
      }),
    );
  }, [locationsRef, refetchLocation]);

  return (
    <WorkspaceContext.Provider
      value={{
        loading: !(
          didLoadStatusData &&
          Object.keys(locationStatuses).every((locationName) => locationEntriesData[locationName])
        ),
        locationEntries,
        allRepos,
        visibleRepos,
        toggleVisible,
        setVisible,
        setHidden,

        data: locationEntriesData,
        refetch,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

function getLocations(d: CodeLocationStatusQuery | undefined | null) {
  const locations =
    d?.locationStatusesOrError?.__typename === 'WorkspaceLocationStatusEntries'
      ? d?.locationStatusesOrError.entries
      : [];

  return locations.reduce(
    (accum, loc) => {
      accum[loc.name] = loc;
      return accum;
    },
    {} as Record<string, (typeof locations)[0]>,
  );
}

export function locationWorkspaceKey(name: string) {
  return `/LocationWorkspace/${name}`;
}

/**
 * useVisibleRepos returns `{reposForKeys, toggleVisible, setVisible, setHidden}` and internally
 * mirrors the current selection into localStorage so that the default selection in new browser
 * windows is the repo currently active in your session.
 */
const validateHiddenKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);

const useVisibleRepos = (
  allRepos: DagsterRepoOption[],
): {
  visibleRepos: DagsterRepoOption[];
  toggleVisible: SetVisibleOrHiddenFn;
  setVisible: SetVisibleOrHiddenFn;
  setHidden: SetVisibleOrHiddenFn;
} => {
  const {basePath} = React.useContext(AppContext);

  const [hiddenKeys, setHiddenKeys] = useStateWithStorage<string[]>(
    basePath + ':' + HIDDEN_REPO_KEYS,
    validateHiddenKeys,
  );

  const hiddenKeysJSON = JSON.stringify([...hiddenKeys.sort()]);

  const toggleVisible = React.useCallback(
    (repoAddresses: RepoAddress[]) => {
      repoAddresses.forEach((repoAddress) => {
        const key = `${repoAddress.name}:${repoAddress.location}`;

        setHiddenKeys((current) => {
          let nextHiddenKeys = [...(current || [])];
          if (nextHiddenKeys.includes(key)) {
            nextHiddenKeys = nextHiddenKeys.filter((k) => k !== key);
          } else {
            nextHiddenKeys = [...nextHiddenKeys, key];
          }
          return nextHiddenKeys;
        });
      });
    },
    [setHiddenKeys],
  );

  const setVisible = React.useCallback(
    (repoAddresses: RepoAddress[]) => {
      const keysToShow = new Set(
        repoAddresses.map((repoAddress) => `${repoAddress.name}:${repoAddress.location}`),
      );
      setHiddenKeys((current) => {
        return current?.filter((key) => !keysToShow.has(key));
      });
    },
    [setHiddenKeys],
  );

  const setHidden = React.useCallback(
    (repoAddresses: RepoAddress[]) => {
      const keysToHide = new Set(
        repoAddresses.map((repoAddress) => `${repoAddress.name}:${repoAddress.location}`),
      );
      setHiddenKeys((current) => {
        const updatedSet = new Set([...(current || []), ...keysToHide]);
        return Array.from(updatedSet);
      });
    },
    [setHiddenKeys],
  );

  const visibleRepos = React.useMemo(() => {
    // If there's only one repo, skip the local storage check -- we have to show this one.
    if (allRepos.length === 1) {
      return allRepos;
    }
    const hiddenKeys = new Set(JSON.parse(hiddenKeysJSON));
    return allRepos.filter((o) => !hiddenKeys.has(getRepositoryOptionHash(o)));
  }, [allRepos, hiddenKeysJSON]);

  return {visibleRepos, toggleVisible, setVisible, setHidden};
};

// Public

const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;
export const useRepositoryOptions = () => {
  const {allRepos: options, loading} = React.useContext(WorkspaceContext);
  return {options, loading};
};

export const useRepository = (repoAddress: RepoAddress | null) => {
  const {options} = useRepositoryOptions();
  return findRepositoryAmongOptions(options, repoAddress) || null;
};

export const useJob = (repoAddress: RepoAddress | null, jobName: string | null) => {
  const repo = useRepository(repoAddress);
  return repo?.repository.pipelines.find((pipelineOrJob) => pipelineOrJob.name === jobName) || null;
};

export const findRepositoryAmongOptions = (
  options: DagsterRepoOption[],
  repoAddress: RepoAddress | null,
) => {
  return repoAddress
    ? options.find(
        (option) =>
          option.repository.name === repoAddress.name &&
          option.repositoryLocation.name === repoAddress.location,
      )
    : null;
};

export const useActivePipelineForName = (pipelineName: string, snapshotId?: string) => {
  const {options} = useRepositoryOptions();
  const reposWithMatch = findRepoContainingPipeline(options, pipelineName, snapshotId);
  if (reposWithMatch[0]) {
    const match = reposWithMatch[0];
    return match.repository.pipelines.find((pipeline) => pipeline.name === pipelineName) || null;
  }
  return null;
};

export const getFeatureFlagForCodeLocation = (
  locationEntries: WorkspaceLocationNodeFragment[],
  locationName: string,
  flagName: string,
) => {
  const matchingLocation = locationEntries.find(({id}) => id === locationName);
  if (matchingLocation) {
    const {featureFlags} = matchingLocation;
    const matchingFlag = featureFlags.find(({name}) => name === flagName);
    if (matchingFlag) {
      return matchingFlag.enabled;
    }
  }
  return false;
};

export const useFeatureFlagForCodeLocation = (locationName: string, flagName: string) => {
  const {locationEntries} = useContext(WorkspaceContext);
  return getFeatureFlagForCodeLocation(locationEntries, locationName, flagName);
};

export const isThisThingAJob = (repo: DagsterRepoOption | null, pipelineOrJobName: string) => {
  const pipelineOrJob = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineOrJobName,
  );
  return !!pipelineOrJob?.isJob;
};

export const isThisThingAnAssetJob = (
  repo: DagsterRepoOption | null,
  pipelineOrJobName: string,
) => {
  const pipelineOrJob = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineOrJobName,
  );
  return !!pipelineOrJob?.isAssetJob;
};

export const buildPipelineSelector = (
  repoAddress: RepoAddress | null,
  pipelineName: string,
  solidSelection?: string[],
) => {
  const repositorySelector = {
    repositoryName: repoAddress?.name || '',
    repositoryLocationName: repoAddress?.location || '',
  };

  return {
    ...repositorySelector,
    pipelineName,
    solidSelection,
  } as PipelineSelector;
};

export const optionToRepoAddress = (option: DagsterRepoOption) =>
  buildRepoAddress(option.repository.name, option.repository.location.name);

export function repoLocationToRepos(repositoryLocation: RepositoryLocation) {
  return repositoryLocation.repositories.map((repository) => {
    return {repository, repositoryLocation};
  });
}
