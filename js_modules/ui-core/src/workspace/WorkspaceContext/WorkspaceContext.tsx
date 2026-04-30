import sortBy from 'lodash/sortBy';
import React, {useCallback, useContext, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {RecoilRoot, useSetRecoilState} from 'recoil';

import {RawWorkspaceAssetsResponse} from './WorkspaceLocationAssetsFetcher';
import {WorkspaceManager} from './WorkspaceManager';
import {
  LocationStatusEntryFragment,
  LocationWorkspaceAssetsManifestQuery,
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceQuery,
  PartialWorkspaceLocationNodeFragment,
  WorkspaceAssetFragment,
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
import {tokenForAssetKey} from '../../asset-graph/Utils';
import type {AssetNodeKeyFragment} from '../../asset-graph/types/AssetNode.types';
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
  const {localCacheIdPrefix, shouldUseAssetManifestForWorkspace} = useContext(AppContext);
  const client = useApolloClient();
  const getData = useGetData();
  const shouldUseAssetManifest = !!shouldUseAssetManifestForWorkspace;

  const [locationWorkspaceData, setLocationWorkspaceData] =
    useState<Record<string, LocationWorkspaceQuery>>(EMPTY_DATA);
  const [rawAssetEntries, setRawAssetEntries] =
    useState<Record<string, RawWorkspaceAssetsResponse>>(EMPTY_DATA);
  const [locationStatuses, setLocationStatuses] =
    useState<Record<string, LocationStatusEntryFragment>>(EMPTY_DATA);

  const assetEntries = useMemo<Record<string, LocationWorkspaceAssetsQuery>>(() => {
    // The fetcher emits whichever shape matches the query it issued, so the
    // shouldUseAssetManifest flag is the source of truth for which branch of
    // RawWorkspaceAssetsResponse a value belongs to. We narrow with that flag
    // and transform manifest dicts to the typed shape so downstream consumers
    // see a single uniform type.
    const result: Record<string, LocationWorkspaceAssetsQuery> = {};
    for (const [key, raw] of Object.entries(rawAssetEntries)) {
      result[key] = shouldUseAssetManifest
        ? transformManifestResponse(narrowToManifestResponse(raw))
        : narrowToTypedResponse(raw);
    }
    return result;
  }, [rawAssetEntries, shouldUseAssetManifest]);

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
    let loadingAssets = rawAssetEntries === EMPTY_DATA;
    loadingNonAssets =
      loadingNonAssets ||
      Object.keys(locationStatuses).some((key) => {
        return !locationWorkspaceData[key];
      });
    loadingAssets =
      loadingAssets ||
      Object.keys(locationStatuses).some((key) => {
        return !rawAssetEntries[key];
      });
    return {loading: loadingNonAssets || loadingAssets, loadingNonAssets, loadingAssets};
  }, [locationStatuses, locationWorkspaceData, rawAssetEntries]);

  const managerRef = useRef<WorkspaceManager | null>(null);

  useLayoutEffect(() => {
    const manager = new WorkspaceManager({
      client,
      localCacheIdPrefix,
      getData,
      setCodeLocationStatusAtom,
      shouldUseAssetManifest,
      setData: ({locationStatuses, locationEntries, assetEntries}) => {
        if (locationEntries) {
          setLocationWorkspaceData(locationEntries);
        }
        if (assetEntries) {
          setRawAssetEntries(assetEntries);
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
  }, [client, localCacheIdPrefix, getData, setCodeLocationStatusAtom, shouldUseAssetManifest]);

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

// Narrows RawWorkspaceAssetsResponse based on the runtime invariant that the
// fetcher emits whichever shape matches the query it issued. The shouldUseAssetManifest
// flag is the source of truth; we centralize the cast here so the call site stays
// readable.
function narrowToManifestResponse(
  raw: RawWorkspaceAssetsResponse,
): LocationWorkspaceAssetsManifestQuery {
  return raw as LocationWorkspaceAssetsManifestQuery;
}

function narrowToTypedResponse(raw: RawWorkspaceAssetsResponse): LocationWorkspaceAssetsQuery {
  return raw as LocationWorkspaceAssetsQuery;
}

// Re-derives `dependedByKeys` and `repository` for every asset in a manifest
// repo, instead of trusting whatever the server emitted on the manifest dict.
// This lets us shrink the manifest payload on the server (drop both fields
// from the asset manifest serializer) without changing anything on the client.
//
// - `dependedByKeys`: built from a per-repo reverse index over `dependencyKeys`,
//   matching the server's per-repo `remote_node.child_keys` resolver — children
//   outside the same repository were never included.
// - `repository`: copied from the parent `Repository` / `RepositoryLocation`,
//   which the manifest query already returns at the surrounding levels.
function deriveAssetNodes(
  rawAssetNodes: WorkspaceAssetFragment[],
  repo: {id: string; name: string},
  location: {id: string; name: string},
): WorkspaceAssetFragment[] {
  const repository: WorkspaceAssetFragment['repository'] = {
    __typename: 'Repository',
    id: repo.id,
    name: repo.name,
    location: {
      __typename: 'RepositoryLocation',
      id: location.id,
      name: location.name,
    },
  };
  const childrenByParent = new Map<string, AssetNodeKeyFragment[]>();
  for (const node of rawAssetNodes) {
    for (const dep of node.dependencyKeys) {
      const parentToken = tokenForAssetKey(dep);
      const list = childrenByParent.get(parentToken);
      if (list) {
        list.push(node.assetKey);
      } else {
        childrenByParent.set(parentToken, [node.assetKey]);
      }
    }
  }
  return rawAssetNodes.map((node) => ({
    ...node,
    dependedByKeys: childrenByParent.get(tokenForAssetKey(node.assetKey)) ?? [],
    repository,
  }));
}

function transformManifestResponse(
  raw: LocationWorkspaceAssetsManifestQuery,
): LocationWorkspaceAssetsQuery {
  const entry = raw.workspaceLocationEntryOrError;
  if (!entry) {
    return {__typename: 'Query', workspaceLocationEntryOrError: null};
  }
  if (entry.__typename === 'PythonError') {
    return {__typename: 'Query', workspaceLocationEntryOrError: entry};
  }
  const locationOrLoadError = entry.locationOrLoadError;
  if (!locationOrLoadError) {
    return {
      __typename: 'Query',
      workspaceLocationEntryOrError: {...entry, locationOrLoadError: null},
    };
  }
  if (locationOrLoadError.__typename === 'PythonError') {
    return {
      __typename: 'Query',
      workspaceLocationEntryOrError: {...entry, locationOrLoadError},
    };
  }
  return {
    __typename: 'Query',
    workspaceLocationEntryOrError: {
      ...entry,
      locationOrLoadError: {
        ...locationOrLoadError,
        repositories: locationOrLoadError.repositories.map((repo) => {
          const {assetManifest, ...rest} = repo;
          // assetManifest is GenericScalar (any | null) on the wire. The backend
          // serializer guarantees its dicts match the WorkspaceAssetFragment shape;
          // we still defend against a non-array landing here.
          const rawAssetNodes: WorkspaceAssetFragment[] = Array.isArray(assetManifest)
            ? assetManifest
            : [];
          const assetNodes = deriveAssetNodes(rawAssetNodes, rest, locationOrLoadError);
          return {...rest, assetNodes};
        }),
      },
    },
  };
}
