import {Box} from '@dagster-io/ui-components';
import React, {useContext, useEffect, useState} from 'react';

import {GraphNode} from './Utils';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {AssetFilterState} from '../assets/useAssetDefinitionFilterState';
import {ChangeReason} from '../graphql/types';
import {useFilters} from '../ui/Filters';
import {useAssetGroupFilter, useAssetGroupsForAssets} from '../ui/Filters/useAssetGroupFilter';
import {useAssetOwnerFilter, useAssetOwnersForAssets} from '../ui/Filters/useAssetOwnerFilter';
import {useAssetTagFilter, useAssetTagsForAssets} from '../ui/Filters/useAssetTagFilter';
import {useChangedFilter} from '../ui/Filters/useChangedFilter';
import {useCodeLocationFilter} from '../ui/Filters/useCodeLocationFilter';
import {
  useAssetKindTagsForAssets,
  useComputeKindTagFilter,
} from '../ui/Filters/useComputeKindTagFilter';
import {FilterObject, FilterTag, FilterTagHighlightedText} from '../ui/Filters/useFilter';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
  isGlobalGraph: boolean;
  assetFilterState?: AssetFilterState;
  loading: boolean;
};

const defaultState = {filters: {}} as Partial<AssetFilterState> & {
  filters: Partial<AssetFilterState['filters']>;
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

  const {allRepos, visibleRepos} = useContext(WorkspaceContext);

  const {
    filters: {changedInBranch, computeKindTags, repos, owners, groups, tags, selectAllFilters},
    setAssetTags,
    setChangedInBranch,
    setComputeKindTags,
    setGroups,
    setOwners,
    setRepos,
    setSelectAllFilters,
  } = assetFilterState || defaultState;

  const reposFilter = useCodeLocationFilter(repos && setRepos ? {repos, setRepos} : undefined);

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

  const tagsFilter = useAssetTagFilter({
    allAssetTags,
    tags: selectAllFilters.includes('tags') ? allAssetTags : tags,
    setTags: setAssetTags,
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
      ['repos', visibleRepos, allRepos] as const,
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
    visibleRepos,
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
  filters.push(tagsFilter);
  filters.push(ownerFilter);
  const {button, activeFiltersJsx} = useFilters({filters});
  if (!filters.length) {
    return {button: null, activeFiltersJsx: null};
  }

  return {
    button,
    filterBar:
      activeFiltersJsx.length || explorerPath ? (
        <Box padding={{vertical: 8, horizontal: 12}} flex={{gap: 12}}>
          {' '}
          {activeFiltersJsx}
          {explorerPath ? (
            <FilterTag
              label={
                <Box flex={{direction: 'row', alignItems: 'center'}}>
                  Asset selection is&nbsp;
                  <FilterTagHighlightedText tooltipText={explorerPath}>
                    {explorerPath}
                  </FilterTagHighlightedText>
                </Box>
              }
              onRemove={clearExplorerPath}
            />
          ) : null}
        </Box>
      ) : null,
  };
}
