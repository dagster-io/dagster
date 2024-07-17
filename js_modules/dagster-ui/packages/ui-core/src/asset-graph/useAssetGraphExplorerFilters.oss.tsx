import React, {useContext, useEffect, useState} from 'react';

import {AssetGraphFilterBar} from './AssetGraphFilterBar';
import {GraphNode} from './Utils';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {AssetFilterState} from '../assets/useAssetDefinitionFilterState.oss';
import {isCanonicalStorageKindTag} from '../graph/KindTags';
import {ChangeReason} from '../graphql/types';
import {useFilters} from '../ui/BaseFilters';
import {FilterObject} from '../ui/BaseFilters/useFilter';
import {useAssetGroupFilter, useAssetGroupsForAssets} from '../ui/Filters/useAssetGroupFilter';
import {useAssetOwnerFilter, useAssetOwnersForAssets} from '../ui/Filters/useAssetOwnerFilter';
import {useAssetTagFilter, useAssetTagsForAssets} from '../ui/Filters/useAssetTagFilter';
import {useChangedFilter} from '../ui/Filters/useChangedFilter';
import {useCodeLocationFilter} from '../ui/Filters/useCodeLocationFilter';
import {
  useAssetKindTagsForAssets,
  useComputeKindTagFilter,
} from '../ui/Filters/useComputeKindTagFilter';
import {useStorageKindFilter} from '../ui/Filters/useStorageKindFilter';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
  isGlobalGraph: boolean;
  assetFilterState?: AssetFilterState;
  loading: boolean;
};

const defaultState: AssetFilterState = {
  filters: {
    changedInBranch: [],
    computeKindTags: [],
    groups: [],
    owners: [],
    repos: [],
    selectAllFilters: [],
    tags: [],
    storageKindTags: [],
  },
  setAssetTags: () => {},
  setChangedInBranch: () => {},
  setComputeKindTags: () => {},
  setFilters: () => {},
  setGroups: () => {},
  setOwners: () => {},
  setRepos: () => {},
  setSelectAllFilters: () => {},
  filterFn: () => true,
  setStorageKindTags: () => {},
};

export function useAssetGraphExplorerFilters({
  nodes,
  isGlobalGraph,
  explorerPath,
  loading,
  clearExplorerPath,
  assetFilterState,
}: Props) {
  const allAssetTags = useAssetTagsForAssets(nodes);

  const {allRepos} = useContext(WorkspaceContext);

  const {
    filters: {
      changedInBranch,
      computeKindTags,
      repos,
      owners,
      groups,
      tags,
      storageKindTags,
      selectAllFilters,
    },
    setAssetTags,
    setChangedInBranch,
    setComputeKindTags,
    setGroups,
    setOwners,
    setRepos,
    setSelectAllFilters,
    setStorageKindTags,
  } = assetFilterState || defaultState;

  const reposFilter = useCodeLocationFilter(repos ? {repos, setRepos} : undefined);

  const changedFilter = useChangedFilter({changedInBranch, setChangedInBranch});

  const allAssetGroups = useAssetGroupsForAssets(nodes);

  const groupsFilter = useAssetGroupFilter({
    assetGroups: selectAllFilters.includes('groups') ? allAssetGroups : groups,
    allAssetGroups,
    setGroups,
  });

  const allComputeKindTags = useAssetKindTagsForAssets(nodes);

  const kindTagsFilter = useComputeKindTagFilter({
    allComputeKindTags,
    computeKindTags: selectAllFilters.includes('computeKindTags')
      ? allComputeKindTags
      : computeKindTags,
    setComputeKindTags,
  });

  const allStorageKindTags = allAssetTags.filter(isCanonicalStorageKindTag);
  const allNonStorageKindTags = allAssetTags.filter((tag) => !isCanonicalStorageKindTag(tag));

  const tagsFilter = useAssetTagFilter({
    allAssetTags: allNonStorageKindTags,
    tags: selectAllFilters.includes('tags') ? allAssetTags : tags,
    setTags: setAssetTags,
  });

  const storageKindTagsFilter = useStorageKindFilter({
    allAssetStorageKindTags: allStorageKindTags,
    storageKindTags: selectAllFilters.includes('storageKindTags')
      ? allStorageKindTags
      : storageKindTags,
    setStorageKindTags,
  });

  const allAssetOwners = useAssetOwnersForAssets(nodes);
  const ownerFilter = useAssetOwnerFilter({
    allAssetOwners,
    owners: selectAllFilters.includes('owners') ? allAssetOwners : owners,
    setOwners,
  });

  const [didWaitAfterLoading, setDidWaitAfterLoading] = useState(false);

  useEffect(() => {
    if (loading) {
      return;
    }
    if (!didWaitAfterLoading) {
      // Wait for a render frame because the graphData is set in a useEffect in response to the data loading...
      requestAnimationFrame(() => setDidWaitAfterLoading(true));
      return;
    }
    let nextAllFilters = [...selectAllFilters];

    let didChange = false;

    [
      ['owners', owners, allAssetOwners] as const,
      ['tags', tags, allAssetTags] as const,
      ['computeKindTags', computeKindTags, allComputeKindTags] as const,
      ['groups', groups, allAssetGroups] as const,
      ['changedInBranch', changedInBranch, Object.values(ChangeReason)] as const,
      ['repos', repos, allRepos] as const,
    ].forEach(([key, activeItems, allItems]) => {
      if (!allItems.length) {
        return;
      }
      if (activeItems.length !== allItems.length) {
        if (selectAllFilters.includes(key)) {
          didChange = true;
          nextAllFilters = nextAllFilters.filter((filter) => filter !== key);
        }
      } else if (activeItems.length && !selectAllFilters.includes(key)) {
        didChange = true;
        nextAllFilters.push(key);
      }
    });

    if (didChange) {
      setSelectAllFilters?.(nextAllFilters);
    }
  }, [
    loading,
    owners,
    allAssetOwners,
    selectAllFilters,
    setSelectAllFilters,
    tags,
    allAssetTags,
    computeKindTags,
    allComputeKindTags,
    groups,
    allAssetGroups,
    changedInBranch,
    repos,
    allRepos,
    didWaitAfterLoading,
  ]);

  const filters: FilterObject[] = [];

  if (allRepos.length > 1 && isGlobalGraph) {
    filters.push(reposFilter);
  }
  if (allAssetGroups) {
    filters.push(groupsFilter);
  }
  const {isBranchDeployment} = React.useContext(CloudOSSContext);
  if (changedInBranch && isBranchDeployment) {
    filters.push(changedFilter);
  }
  filters.push(kindTagsFilter);
  filters.push(storageKindTagsFilter);
  filters.push(tagsFilter);
  filters.push(ownerFilter);
  const {button, activeFiltersJsx} = useFilters({filters});

  return {
    computeKindTagsFilter: kindTagsFilter,
    storageKindTagsFilter,
    button: filters.length ? button : null,
    activeFiltersJsx,
    filterBar: (
      <AssetGraphFilterBar
        activeFiltersJsx={activeFiltersJsx}
        explorerPath={explorerPath}
        clearExplorerPath={clearExplorerPath}
      />
    ),
  };
}
