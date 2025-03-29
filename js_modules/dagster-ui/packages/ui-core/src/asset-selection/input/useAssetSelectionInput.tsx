import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {AssetGraphAssetSelectionInput} from 'shared/asset-graph/AssetGraphAssetSelectionInput.oss';
import {AssetSelectionInput} from 'shared/asset-selection/input/AssetSelectionInput.oss';
import {useAssetSelectionState} from 'shared/asset-selection/useAssetSelectionState.oss';
import {FilterableAssetDefinition} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {featureEnabled} from '../../app/Flags';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {useAssetSelectionFiltering} from '../useAssetSelectionFiltering';
export const useAssetSelectionInput = <
  T extends {
    id: string;
    key: {path: Array<string>};
    definition?: FilterableAssetDefinition | null;
  },
>({
  assets,
  assetsLoading,
  onErrorStateChange,
}: {
  assets: T[];
  assetsLoading?: boolean;
  onErrorStateChange?: (errors: SyntaxError[]) => void;
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
        onErrorStateChange={onErrorStateChange}
      />
    );
  }

  return {filterInput, loading, filtered: filtered as T[], assetSelection, setAssetSelection};
};
