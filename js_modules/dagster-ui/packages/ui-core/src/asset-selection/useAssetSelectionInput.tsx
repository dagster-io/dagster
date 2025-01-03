import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {AssetGraphAssetSelectionInput} from 'shared/asset-graph/AssetGraphAssetSelectionInput.oss';
import {AssetSelectionInput} from 'shared/asset-selection/input/AssetSelectionInput.oss';
import {useAssetSelectionState} from 'shared/asset-selection/useAssetSelectionState.oss';
import {FilterableAssetDefinition} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {useAssetSelectionFiltering} from './useAssetSelectionFiltering';
import {featureEnabled} from '../app/Flags';

export const useAssetSelectionInput = <
  T extends {
    id: string;
    key: {path: Array<string>};
    definition?: FilterableAssetDefinition | null;
  },
>({
  assets,
  assetsLoading,
}: {
  assets: T[];
  assetsLoading?: boolean;
}) => {
  const [assetSelection, setAssetSelection] = useAssetSelectionState();

  const {graphQueryItems, loading, filtered} = useAssetSelectionFiltering({
    assetSelection,
    assets,
    loading: !!assetsLoading,
  });

  let filterInput = (
    <AssetGraphAssetSelectionInput
      items={graphQueryItems}
      value={assetSelection}
      placeholder="Type an asset subset…"
      onChange={setAssetSelection}
      popoverPosition="bottom-left"
    />
  );

  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    filterInput = (
      <AssetSelectionInput
        value={assetSelection}
        onChange={setAssetSelection}
        assets={graphQueryItems}
      />
    );
  }

  return {filterInput, loading, filtered, assetSelection, setAssetSelection};
};
