import sortBy from 'lodash/sortBy';
import React, {useCallback, useContext, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {RecoilRoot, useSetRecoilState} from 'recoil';

import {WorkspaceManager} from './WorkspaceManager';
import {
  FullWorkspaceLocationNodeFragment,
  LocationStatusEntryFragment,
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceQuery,
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

interface WorkspaceState {
  loading: boolean;
  locationEntries: WorkspaceRepositoryLocationNode[];
  locationStatuses: Record<string, LocationStatusEntryFragment>;
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
  loading: false,
  locationEntries: [],
  locationStatuses: {},
  setVisible: () => {},
  setHidden: () => {},
});

export const WorkspaceProvider = ({children}: {children: React.ReactNode}) => {
  return (
    <RecoilRoot>
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
      {} as Record<string, WorkspaceLocationNodeFragment | PythonErrorFragment>,
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
    const result: Record<
      string,
      FullWorkspaceLocationNodeFragment | WorkspaceLocationNodeFragment | PythonErrorFragment
    > = {};
    Object.entries(locationEntryData).forEach(([key, data]) => {
      if (
        assetLocationEntries[key] &&
        data.__typename === 'WorkspaceLocationEntry' &&
        assetLocationEntries[key].__typename === 'WorkspaceLocationEntry'
      ) {
        result[key] = mergeWorkspaceData(data, assetLocationEntries[key]);
      } else {
        result[key] = data;
      }
    });
    return result;
  }, [locationEntryData, assetLocationEntries]);

  const loading = useMemo(() => {
    if (locationWorkspaceData === EMPTY_DATA || assetLocationEntries === EMPTY_DATA) {
      return true;
    }
    return Object.keys(locationStatuses).some((key) => {
      return !locationWorkspaceData[key] || !assetLocationEntries[key];
    });
  }, [locationStatuses, locationWorkspaceData, assetLocationEntries]);

  const managerRef = useRef<WorkspaceManager | null>(null);

  useLayoutEffect(() => {
    const manager = new WorkspaceManager({
      client,
      localCacheIdPrefix,
      getData,
      setCodeLocationStatusAtom,
      setData: ({locationStatuses, locationEntries, assetEntries}) => {
        setLocationWorkspaceData(locationEntries);
        setAssetEntries(assetEntries);
        setLocationStatuses(locationStatuses);
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
        acc.push(ensureAssetsData(data));
      }
      return acc;
    }, [] as Array<FullWorkspaceLocationNodeFragment>);
  }, [fullLocationEntryData]);

  const allRepos = useAllRepos(locationEntries);

  const {visibleRepos, toggleVisible, setVisible, setHidden} = useVisibleRepos(allRepos);

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

function ensureAssetsData(
  data: WorkspaceLocationNodeFragment | FullWorkspaceLocationNodeFragment,
): FullWorkspaceLocationNodeFragment {
  const locationOrLoadError = data.locationOrLoadError;
  if (locationOrLoadError?.__typename === 'RepositoryLocation') {
    let needsAssets = false;
    locationOrLoadError.repositories.some((repo) => {
      if (!('assetNodes' in repo)) {
        needsAssets = true;
      }
    });
    if (needsAssets) {
      return {
        ...data,
        locationOrLoadError: {
          ...locationOrLoadError,
          repositories: locationOrLoadError.repositories.map((repo) => ({
            ...repo,
            assetNodes: [],
            assetGroups: [],
          })) as any,
        },
      };
    }
  }
  return data as FullWorkspaceLocationNodeFragment;
}
