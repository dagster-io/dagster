import {useAssetCatalogFiltering} from 'shared/assets/useAssetCatalogFiltering.oss';

import {AssetGraphFilterBar} from './AssetGraphFilterBar';
import {GraphNode} from './Utils';

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
  isGlobalGraph: boolean;
  loading: boolean;
};

export function useAssetGraphExplorerFilters({
  nodes,
  isGlobalGraph,
  explorerPath,
  loading,
  clearExplorerPath,
}: Props) {
  const {filterButton, groupsFilter, activeFiltersJsx, kindFilter, filterFn} =
    useAssetCatalogFiltering({
      assets: nodes,
      includeRepos: isGlobalGraph,
      loading,
    });

  return {
    kindFilter,
    groupsFilter,
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
