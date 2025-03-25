import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {AssetGraphFilterBar} from 'shared/asset-graph/AssetGraphFilterBar.oss';
import {useAssetCatalogFiltering} from 'shared/assets/useAssetCatalogFiltering.oss';

import {AssetGraphViewType, GraphNode} from './Utils';
import {featureEnabled} from '../app/Flags';

export type Props = {
  nodes: GraphNode[];
  setAssetSelection: (selection: string) => void;
  assetSelection: string;
  viewType: AssetGraphViewType;
  loading: boolean;
};

export function useAssetGraphExplorerFilters({
  nodes,
  viewType,
  assetSelection,
  loading,
  setAssetSelection,
}: Props) {
  const ret = useAssetCatalogFiltering({
    assets: nodes,
    includeRepos: viewType === AssetGraphViewType.GLOBAL,
    loading,
    enabled: !featureEnabled(FeatureFlag.flagSelectionSyntax),
  });

  return {
    ...ret,
    button: ret.filterButton,
    filterBar: (
      <AssetGraphFilterBar
        activeFiltersJsx={ret.activeFiltersJsx}
        assetSelection={assetSelection}
        setAssetSelection={setAssetSelection}
      />
    ),
  };
}
