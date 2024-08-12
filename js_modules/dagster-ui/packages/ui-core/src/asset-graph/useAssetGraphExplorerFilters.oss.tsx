import React from 'react';
import {useAssetCatalogFiltering} from 'shared/assets/useAssetCatalogFiltering.oss';
import {AssetFilterState} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {AssetGraphFilterBar} from './AssetGraphFilterBar';
import {GraphNode} from './Utils';

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
  isGlobalGraph: boolean;
  assetFilterState?: AssetFilterState;
  loading: boolean;
};

export function useAssetGraphExplorerFilters({
  nodes,
  isGlobalGraph,
  explorerPath,
  loading,
  clearExplorerPath,
}: Props) {
  const {filterButton, computeKindFilter, storageKindFilter, activeFiltersJsx, filterFn} =
    useAssetCatalogFiltering({
      assets: nodes,
      includeRepos: isGlobalGraph,
      loading,
    });

  return {
    computeKindTagsFilter: computeKindFilter,
    storageKindTagsFilter: storageKindFilter,
    button: filterButton,
    filterFn,
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
