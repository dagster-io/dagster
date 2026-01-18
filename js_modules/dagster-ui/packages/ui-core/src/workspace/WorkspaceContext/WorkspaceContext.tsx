import sortBy from 'lodash/sortBy';
import React, {useCallback, useContext, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {RecoilRoot, useSetRecoilState} from 'recoil';

import {WorkspaceManager} from './WorkspaceManager';
import {
  LocationStatusEntryFragment,
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceQuery,
  PartialWorkspaceLocationNodeFragment,
  WorkspaceLocationAssetsEntryFragment,
  WorkspaceLocationNodeFragment,
  WorkspaceScheduleFragment,
  WorkspaceSensorFragment,
} from './types/WorkspaceQueries.types';
import {
  DagsterRepoOption,
  SetVisibleOrHiddenFn,
  mergeWorkspaceData,
  repoLocationToRepos,
  useVisibleRepos,
} from './util';
import {useApolloClient} from '../../apollo-client';
import {AppContext} from '../../app/AppContext';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {codeLocationStatusAtom} from '../../nav/useCodeLocationsStatus';
import {useGetData} from '../../search/useIndexedDBCachedQuery';

export const HIDDEN_REPO_KEYS = 'dagster.hidden-repo-keys';

export type WorkspaceRepositorySensor = WorkspaceSensorFragment;
export type WorkspaceRepositorySchedule = WorkspaceScheduleFragment;
export type WorkspaceRepositoryLocationNode = WorkspaceLocationNodeFragment;

export interface WorkspaceState {
  locationEntries: WorkspaceLocationNodeFragment[];
  locationStatuses: Record<string, LocationStatusEntryFragment>;
  loadingNonAssets: boolean;
  loadingAssets: boolean;
  assetEntries: Record<string, LocationWorkspaceAssetsQuery>;
  allRepos: DagsterRepoOption[];
  visibleRepos: DagsterRepoOption[];
  data: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>;
  toggleVisible: SetVisibleOrHiddenFn;
  setVisible: SetVisibleOrHiddenFn;
  setHidden: SetVisibleOrHiddenFn;
  refetch: () => Promise<void>;
}

export const WorkspaceContext = React.createContext<WorkspaceState>({
  allRepos: [],
  visibleRepos: [],
  data: {},
  refetch: () => Promise.reject<any>(),
  toggleVisible: () => {},
  loadingNonAssets: true,
  loadingAssets: true,
  assetEntries: {},
  locationEntries: [],
  locationStatuses: {},
  setVisible: () => {},
  setHidden: () => {},
});

export const WorkspaceProvider = ({children}: {children: React.ReactNode}) => {
  return (
    <RecoilRoot override={false}>
      <WorkspaceProviderImpl>{children}</WorkspaceProviderImpl>
    </RecoilRoot>
  );
};

const EMPTY_DATA = {};
const WorkspaceProviderImpl = ({children}: {children: React.ReactNode}) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  const client = useApolloClient();
  const getData = useGetData();

  const [locationWorkspaceData, setLocationWorkspaceData] =
    useState<Record<string, LocationWorkspaceQuery>>(EMPTY_DATA);
  const [assetEntries, setAssetEntries] =
    useState<Record<string, LocationWorkspaceAssetsQuery>>(EMPTY_DATA);
  const [locationStatuses, setLocationStatuses] =
    useState<Record<string, LocationStatusEntryFragment>>(EMPTY_DATA);

  const setCodeLocationStatusAtom = useSetRecoilState(codeLocationStatusAtom);

  const locationEntryData = useMemo(() => {
    return Object.entries(locationWorkspaceData).reduce(
      (acc, [key, data]) => {
        if (data.workspaceLocationEntryOrError) {
          acc[key] = data.workspaceLocationEntryOrError;
        }
        return acc;
      },
      {} as Record<string, PartialWorkspaceLocationNodeFragment | PythonErrorFragment>,
    );
  }, [locationWorkspaceData]);

  const assetLocationEntries = useMemo(() => {
    return Object.entries(assetEntries).reduce(
      (acc, [key, data]) => {
        if (data.workspaceLocationEntryOrError) {
          acc[key] = data.workspaceLocationEntryOrError;
        }
        return acc;
      },
      {} as Record<string, WorkspaceLocationAssetsEntryFragment | PythonErrorFragment>,
    );
  }, [assetEntries]);

  const fullLocationEntryData = useMemo(() => {
    const result: Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment> = {};
    Object.entries(locationEntryData).forEach(([key, data]) => {
      if (
        assetLocationEntries[key] &&
        data.__typename === 'WorkspaceLocationEntry' &&
        assetLocationEntries[key].__typename === 'WorkspaceLocationEntry'
      ) {
        result[key] = mergeWorkspaceData(data, assetLocationEntries[key]);
      } else if (data.__typename === 'WorkspaceLocationEntry') {
        result[key] = addAssetsData(data);
      } else {
        result[key] = data;
      }
    });
    return result;
  }, [locationEntryData, assetLocationEntries]);

  const {loadingNonAssets, loadingAssets} = useMemo(() => {
    let loadingNonAssets = locationWorkspaceData === EMPTY_DATA;
    let loadingAssets = assetEntries === EMPTY_DATA;
    loadingNonAssets =
      loadingNonAssets ||
      Object.keys(locationStatuses).some((key) => {
        return !locationWorkspaceData[key];
      });
    loadingAssets =
      loadingAssets ||
      Object.keys(locationStatuses).some((key) => {
        return !assetEntries[key];
      });
    return {loading: loadingNonAssets || loadingAssets, loadingNonAssets, loadingAssets};
  }, [locationStatuses, locationWorkspaceData, assetEntries]);

  const managerRef = useRef<WorkspaceManager | null>(null);

  useLayoutEffect(() => {
    const manager = new WorkspaceManager({
      client,
      localCacheIdPrefix,
      getData,
      setCodeLocationStatusAtom,
      setData: ({locationStatuses, locationEntries, assetEntries}) => {
        if (locationEntries) {
          setLocationWorkspaceData(locationEntries);
        }
        if (assetEntries) {
          setAssetEntries(assetEntries);
        }
        if (locationStatuses) {
          setLocationStatuses(locationStatuses);
        }
      },
    });
    managerRef.current = manager;
    return () => {
      manager.destroy();
    };
  }, [client, localCacheIdPrefix, getData, setCodeLocationStatusAtom]);

  const locationEntries = useMemo(() => {
    return Object.values(fullLocationEntryData).reduce((acc, data) => {
      if (data.__typename === 'WorkspaceLocationEntry') {
        acc.push(data);
      }
      return acc;
    }, [] as Array<WorkspaceLocationNodeFragment>);
  }, [fullLocationEntryData]);

  const allRepos = useAllRepos(locationEntries);

  const {visibleRepos, toggleVisible, setVisible, setHidden} = useVisibleRepos(allRepos);

  return (
    <WorkspaceContext.Provider
      value={{
        loadingNonAssets,
        loadingAssets,
        assetEntries,
        locationEntries,
        locationStatuses,
        allRepos,
        visibleRepos,
        toggleVisible,
        setVisible,
        setHidden,
        data: fullLocationEntryData,
        refetch: useCallback(async () => {
          await managerRef.current?.refetchAll();
        }, []),
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

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

function addAssetsData(data: PartialWorkspaceLocationNodeFragment): WorkspaceLocationNodeFragment {
  const locationOrLoadError = data.locationOrLoadError;
  if (locationOrLoadError?.__typename === 'RepositoryLocation') {
    return {
      ...data,
      locationOrLoadError: {
        ...locationOrLoadError,
        repositories: locationOrLoadError.repositories.map((repo) => ({
          ...repo,
          assetNodes: [],
          assetGroups: [],
        })),
      },
    };
  }
  return data as WorkspaceLocationNodeFragment;
}
