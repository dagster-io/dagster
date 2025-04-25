import sortBy from 'lodash/sortBy';
import React, {useContext, useLayoutEffect, useMemo, useState} from 'react';
import {useSetRecoilState} from 'recoil';

import {WorkspaceManager} from './WorkspaceManager';
import {
  LocationStatusEntryFragment,
  LocationWorkspaceQuery,
  WorkspaceLocationNodeFragment,
  WorkspaceScheduleFragment,
  WorkspaceSensorFragment,
} from './types/WorkspaceQueries.types';
import {
  DagsterRepoOption,
  SetVisibleOrHiddenFn,
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
}

export const WorkspaceContext = React.createContext<WorkspaceState>({
  allRepos: [],
  visibleRepos: [],
  data: {},
  toggleVisible: () => {},
  loading: false,
  locationEntries: [],
  locationStatuses: {},
  setVisible: () => {},
  setHidden: () => {},
});

const UNLOADED_CACHED_DATA = {};
export const WorkspaceProvider = ({children}: {children: React.ReactNode}) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  const client = useApolloClient();
  const getData = useGetData();

  const [locationWorkspaceData, setLocationWorkspaceData] =
    useState<Record<string, LocationWorkspaceQuery>>(UNLOADED_CACHED_DATA);

  const [locationStatuses, setLocationStatuses] = useState<
    Record<string, LocationStatusEntryFragment>
  >({});

  const setCodeLocationStatusAtom = useSetRecoilState(codeLocationStatusAtom);

  const loading = useMemo(() => {
    if (locationWorkspaceData === UNLOADED_CACHED_DATA) {
      return true;
    }
    return Object.keys(locationStatuses).some((key) => {
      return !locationWorkspaceData[key];
    });
  }, [locationWorkspaceData, locationStatuses]);

  useLayoutEffect(() => {
    const manager = new WorkspaceManager({
      client,
      localCacheIdPrefix,
      getData,
      setCodeLocationStatusAtom,
      setData: ({locationStatuses, locationEntryData}) => {
        setLocationWorkspaceData(locationEntryData);
        setLocationStatuses(locationStatuses);
      },
    });
    return () => {
      manager.destroy();
    };
  }, [client, localCacheIdPrefix, getData, setCodeLocationStatusAtom]);

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

  const locationEntries = useMemo(() => {
    return Object.values(locationWorkspaceData).reduce((acc, data) => {
      if (data.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry') {
        acc.push(data.workspaceLocationEntryOrError);
      }
      return acc;
    }, [] as Array<WorkspaceLocationNodeFragment>);
  }, [locationWorkspaceData]);

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
