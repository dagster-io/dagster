import {AssetSelectionInput} from '@shared/asset-selection/input/AssetSelectionInput';
import {useAssetSelectionState} from '@shared/asset-selection/useAssetSelectionState';
import {useMemo} from 'react';

import {SyntaxError} from '../../selection/CustomErrorListener';
import {FilterableAssetDefinition, useAssetSelectionFiltering} from '../useAssetSelectionFiltering';
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

  const filterInput = useMemo(() => {
    return (
      <AssetSelectionInput
        value={assetSelection}
        onChange={setAssetSelection}
        assets={graphQueryItems}
        onErrorStateChange={onErrorStateChange}
      />
    );
  }, [assetSelection, graphQueryItems, onErrorStateChange, setAssetSelection]);

  return {filterInput, loading, filtered: filtered as T[], assetSelection, setAssetSelection};
};
