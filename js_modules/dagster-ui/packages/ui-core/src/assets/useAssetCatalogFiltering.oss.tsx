import * as React from 'react';
import {useEffect, useMemo, useState} from 'react';
import {
  FilterableAssetDefinition,
  useAssetDefinitionFilterState,
} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {useAssetGroupSelectorsForAssets} from './AssetGroupSuggest';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {ChangeReason} from '../graphql/types';
import {useFilters} from '../ui/BaseFilters';
import {FilterObject} from '../ui/BaseFilters/useFilter';
import {useAssetGroupFilter} from '../ui/Filters/useAssetGroupFilter';
import {useAssetOwnerFilter, useAssetOwnersForAssets} from '../ui/Filters/useAssetOwnerFilter';
import {useChangedFilter} from '../ui/Filters/useChangedFilter';
import {useCodeLocationFilter} from '../ui/Filters/useCodeLocationFilter';
import {useDefinitionTagFilter, useTagsForAssets} from '../ui/Filters/useDefinitionTagFilter';
import {useAssetKindsForAssets, useKindFilter} from '../ui/Filters/useKindFilter';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

const EMPTY_ARRAY: any[] = [];

const ALL_CHANGED_IN_BRANCH_VALUES = Object.values(ChangeReason);

export function useAssetCatalogFiltering<
  T extends {
    id: string;
    definition?: FilterableAssetDefinition | null;
  },
>({
  assets = EMPTY_ARRAY,
  includeRepos = true,
  loading = false,
  enabled = true,
}: {
  assets: T[] | undefined;
  includeRepos?: boolean;
  loading?: boolean;
  enabled?: boolean;
}) {
  const {
    filters,
    filterFn,
    setAssetTags,
    setChangedInBranch,
    setKinds,
    setGroups,
    setOwners,
    setCodeLocations,
    setSelectAllFilters,
  } = useAssetDefinitionFilterState({isEnabled: enabled});

  const allAssetGroupOptions = useAssetGroupSelectorsForAssets(assets);
  const allAssetOwners = useAssetOwnersForAssets(assets);

  const groupsFilter = useAssetGroupFilter({
    allAssetGroups: allAssetGroupOptions,
    assetGroups: filters.selectAllFilters.includes('groups')
      ? allAssetGroupOptions
      : filters.groups,
    setGroups,
  });
  const changedInBranchFilter = useChangedFilter({
    changedInBranch: filters.selectAllFilters.includes('changedInBranch')
      ? ALL_CHANGED_IN_BRANCH_VALUES
      : filters.changedInBranch,
    setChangedInBranch,
  });

  const ownersFilter = useAssetOwnerFilter({
    allAssetOwners,
    owners: filters.selectAllFilters.includes('owners') ? allAssetOwners : filters.owners,
    setOwners,
  });

  const allKinds = useAssetKindsForAssets(assets);
  const kindFilter = useKindFilter({
    allAssetKinds: allKinds,
    kinds: filters.selectAllFilters.includes('kinds') ? allKinds : filters.kinds,
    setKinds,
  });

  const tags = useTagsForAssets(assets);

  const tagsFilter = useDefinitionTagFilter({
    allTags: tags,
    tags: filters.selectAllFilters.includes('tags') ? tags : filters.tags,
    setTags: setAssetTags,
  });

  const {isBranchDeployment} = React.useContext(CloudOSSContext);
  const {allRepos} = React.useContext(WorkspaceContext);

  const allRepoAddresses = useMemo(() => {
    return allRepos.map((repo) =>
      buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
    );
  }, [allRepos]);

  const reposFilter = useCodeLocationFilter({
    codeLocations: filters.selectAllFilters?.includes('codeLocations')
      ? allRepoAddresses
      : filters.codeLocations,
    setCodeLocations,
  });

  const uiFilters = React.useMemo(() => {
    const uiFilters: FilterObject[] = [groupsFilter, kindFilter, ownersFilter, tagsFilter];
    if (isBranchDeployment) {
      uiFilters.push(changedInBranchFilter);
    }
    if (allRepos.length > 1 && includeRepos) {
      uiFilters.unshift(reposFilter);
    }
    return uiFilters;
  }, [
    allRepos.length,
    changedInBranchFilter,
    kindFilter,
    groupsFilter,
    includeRepos,
    isBranchDeployment,
    ownersFilter,
    reposFilter,
    tagsFilter,
  ]);
  const components = useFilters({filters: uiFilters});

  const isFiltered: boolean = !!Object.values(filters as Record<string, any[]>).some(
    (filter) => filter?.length,
  );

  const [didWaitAfterLoading, setDidWaitAfterLoading] = useState(false);

  useEffect(() => {
    /**
     * This effect handles syncing the `selectAllFilters` query param state with the actual filtering state.
     * eg: If all of the items are selected then we include that key, otherwise we remove it.
     */
    if (loading || !enabled) {
      return;
    }
    if (!didWaitAfterLoading) {
      requestAnimationFrame(() => setDidWaitAfterLoading(true));
      return;
    }
    let nextAllFilters = [...filters.selectAllFilters];

    let didChange = false;

    [
      ['owners', filters.owners, allAssetOwners] as const,
      ['tags', filters.tags, tags] as const,
      ['kinds', filters.kinds, allKinds] as const,
      ['groups', filters.groups, allAssetGroupOptions] as const,
      ['changedInBranch', filters.changedInBranch, Object.values(ChangeReason)] as const,
      ['codeLocations', filters.codeLocations, allRepos] as const,
    ].forEach(([key, activeItems, allItems]) => {
      if (!allItems.length) {
        return;
      }
      if ((activeItems?.length ?? 0) !== allItems.length) {
        // Not all items are included, lets remove the key if its included
        if (filters.selectAllFilters?.includes(key)) {
          didChange = true;
          nextAllFilters = nextAllFilters.filter((filter) => filter !== key);
        }
      } else if (activeItems?.length && !filters.selectAllFilters?.includes(key)) {
        // All items are included, lets add the key since its not already included
        didChange = true;
        nextAllFilters.push(key);
      }
    });

    if (didChange) {
      setSelectAllFilters?.(nextAllFilters);
    }
  }, [
    allAssetGroupOptions,
    allAssetOwners,
    allKinds,
    allRepos,
    didWaitAfterLoading,
    filters,
    loading,
    tags,
    setSelectAllFilters,
    enabled,
  ]);

  const filteredAssets = React.useMemo(
    () => assets.filter((a) => filterFn(a.definition ?? {})),
    [filterFn, assets],
  ) as T[];

  return {
    activeFiltersJsx: components.activeFiltersJsx,
    filterButton: components.button,
    isFiltered,
    filterFn,
    filteredAssets,
    filteredAssetsLoading: false,
    kindFilter,
    groupsFilter,
    renderFilterButton: components.renderButton,
  };
}
