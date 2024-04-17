import {Box} from '@dagster-io/ui-components';
import React, {useContext} from 'react';

import {GraphNode} from './Utils';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {AssetFilterState} from '../assets/useAssetDefinitionFilterState';
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
};

const defaultState = {filters: {}} as Partial<AssetFilterState> & {
  filters: Partial<AssetFilterState['filters']>;
};

export function useAssetGraphExplorerFilters({
  nodes,
  isGlobalGraph,
  explorerPath,
  clearExplorerPath,
  assetFilterState,
}: Props) {
  const allAssetTags = useAssetTagsForAssets(nodes);

  const {allRepos} = useContext(WorkspaceContext);

  const {
    filters: {changedInBranch, computeKindTags, repos, owners, groups, tags},
    setAssetTags,
    setChangedInBranch,
    setComputeKindTags,
    setGroups,
    setOwners,
    setRepos,
  } = assetFilterState || defaultState;

  const reposFilter = useCodeLocationFilter(repos && setRepos ? {repos, setRepos} : undefined);

  const changedFilter = useChangedFilter({changedInBranch, setChangedInBranch});

  const allAssetGroups = useAssetGroupsForAssets(nodes);

  const groupsFilter = useAssetGroupFilter({
    assetGroups: groups,
    allAssetGroups,
    setGroups,
  });

  const allComputeKindTags = useAssetKindTagsForAssets(nodes);

  const kindTagsFilter = useComputeKindTagFilter({
    allComputeKindTags,
    computeKindTags,
    setComputeKindTags,
  });

  const tagsFilter = useAssetTagFilter({
    allAssetTags,
    tags,
    setTags: setAssetTags,
  });

  const allAssetOwners = useAssetOwnersForAssets(nodes);
  const ownerFilter = useAssetOwnerFilter({
    allAssetOwners,
    owners,
    setOwners,
  });

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
