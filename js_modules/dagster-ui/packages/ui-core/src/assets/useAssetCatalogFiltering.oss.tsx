import {TextInput} from '@dagster-io/ui-components';
import * as React from 'react';

import {useAssetGroupSelectorsForAssets} from './AssetGroupSuggest';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {useAssetDefinitionFilterState} from './useAssetDefinitionFilterState';
import {useAssetSearch} from './useAssetSearch';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {isCanonicalStorageKindTag} from '../graph/KindTags';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useFilters} from '../ui/BaseFilters';
import {FilterObject} from '../ui/BaseFilters/useFilter';
import {useAssetGroupFilter} from '../ui/Filters/useAssetGroupFilter';
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

const EMPTY_ARRAY: any[] = [];

export function useAssetCatalogFiltering(
  assets: AssetTableFragment[] | undefined,
  prefixPath: string[],
) {
  const [search, setSearch] = useQueryPersistedState<string | undefined>({queryKey: 'q'});

  const {
    filters,
    filterFn,
    setAssetTags,
    setChangedInBranch,
    setComputeKindTags,
    setGroups,
    setOwners,
    setRepos,
    setStorageKindTags,
  } = useAssetDefinitionFilterState();

  const searchPath = (search || '')
    .replace(/(( ?> ?)|\.|\/)/g, '/')
    .toLowerCase()
    .trim();

  const pathMatches = useAssetSearch(
    searchPath,
    assets ?? (EMPTY_ARRAY as NonNullable<typeof assets>),
  );

  const filtered = React.useMemo(
    () => pathMatches.filter((a) => filterFn(a.definition ?? {})),
    [filterFn, pathMatches],
  );

  const allAssetGroupOptions = useAssetGroupSelectorsForAssets(pathMatches);
  const allComputeKindTags = useAssetKindTagsForAssets(pathMatches);
  const allAssetOwners = useAssetOwnersForAssets(pathMatches);

  const groupsFilter = useAssetGroupFilter({
    allAssetGroups: allAssetGroupOptions,
    assetGroups: filters.groups,
    setGroups,
  });
  const changedInBranchFilter = useChangedFilter({
    changedInBranch: filters.changedInBranch,
    setChangedInBranch,
  });
  const computeKindFilter = useComputeKindTagFilter({
    allComputeKindTags,
    computeKindTags: filters.computeKindTags,
    setComputeKindTags,
  });
  const ownersFilter = useAssetOwnerFilter({
    allAssetOwners,
    owners: filters.owners,
    setOwners,
  });

  const tags = useAssetTagsForAssets(pathMatches);
  const storageKindTags = tags.filter(isCanonicalStorageKindTag);
  const nonStorageKindTags = tags.filter((tag) => !isCanonicalStorageKindTag(tag));

  const tagsFilter = useAssetTagFilter({
    allAssetTags: nonStorageKindTags,
    tags: filters.tags,
    setTags: setAssetTags,
  });
  const storageKindFilter = useStorageKindFilter({
    allAssetStorageKindTags: storageKindTags,
    storageKindTags: filters.storageKindTags,
    setStorageKindTags,
  });

  const uiFilters: FilterObject[] = [
    groupsFilter,
    computeKindFilter,
    storageKindFilter,
    ownersFilter,
    tagsFilter,
  ];
  const {isBranchDeployment} = React.useContext(CloudOSSContext);
  if (isBranchDeployment) {
    uiFilters.push(changedInBranchFilter);
  }
  const {allRepos} = React.useContext(WorkspaceContext);

  const reposFilter = useCodeLocationFilter({repos: filters.repos, setRepos});
  if (allRepos.length > 1) {
    uiFilters.unshift(reposFilter);
  }
  const components = useFilters({filters: uiFilters});

  const filterInput = (
    <TextInput
      value={search || ''}
      style={{width: '30vw', minWidth: 150, maxWidth: 400}}
      placeholder={
        prefixPath.length ? `Filter asset keys in ${prefixPath.join('/')}…` : `Filter asset keys…`
      }
      onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
    />
  );

  const isFiltered: boolean = !!(
    filters.changedInBranch?.length ||
    filters.computeKindTags?.length ||
    filters.storageKindTags?.length ||
    filters.groups?.length ||
    filters.owners?.length ||
    filters.repos?.length
  );

  return {
    searchPath,
    activeFiltersJsx: components.activeFiltersJsx,
    filterButton: components.button,
    filterInput,
    isFiltered,
    filtered,
    computeKindFilter,
    storageKindFilter,
  };
}
