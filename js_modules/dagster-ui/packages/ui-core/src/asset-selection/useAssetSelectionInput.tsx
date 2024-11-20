import {AssetGraphAssetSelectionInput} from 'shared/asset-graph/AssetGraphAssetSelectionInput.oss';
import {useAssetSelectionState} from 'shared/asset-selection/useAssetSelectionState.oss';
import {FilterableAssetDefinition} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {useAssetSelectionFiltering} from './useAssetSelectionFiltering';

export const useAssetSelectionInput = <
  T extends {
    id: string;
    key: {path: Array<string>};
    definition?: FilterableAssetDefinition | null;
  },
>(
  assets: T[],
) => {
  const [assetSelection, setAssetSelection] = useAssetSelectionState();

  const {graphQueryItems, fetchResult, filtered} = useAssetSelectionFiltering({
    assetSelection,
    assets,
  });

  const filterInput = (
    <AssetGraphAssetSelectionInput
      items={graphQueryItems}
      value={assetSelection}
      placeholder="Type an asset subset…"
      onChange={setAssetSelection}
      popoverPosition="bottom-left"
    />
  );

  return {filterInput, fetchResult, filtered, assetSelection, setAssetSelection};
};
