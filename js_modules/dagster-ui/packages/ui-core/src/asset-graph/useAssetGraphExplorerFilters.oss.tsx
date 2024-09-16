import {useAssetCatalogFiltering} from 'shared/assets/useAssetCatalogFiltering.oss';

import {AssetGraphFilterBar} from './AssetGraphFilterBar';
import {AssetGraphViewType, GraphNode} from './Utils';

type Props = {
  nodes: GraphNode[];
  clearExplorerPath: () => void;
  explorerPath: string;
  viewType: AssetGraphViewType;
  loading: boolean;
};

export function useAssetGraphExplorerFilters({
  nodes,
  viewType,
  explorerPath,
  loading,
  clearExplorerPath,
}: Props) {
  const ret = useAssetCatalogFiltering({
    assets: nodes,
    includeRepos: viewType === AssetGraphViewType.GLOBAL,
    loading,
  });

  return {
    ...ret,
    button: ret.filterButton,
    filterBar: (
      <AssetGraphFilterBar
        activeFiltersJsx={ret.activeFiltersJsx}
        explorerPath={explorerPath}
        clearExplorerPath={clearExplorerPath}
      />
    ),
  };
}
