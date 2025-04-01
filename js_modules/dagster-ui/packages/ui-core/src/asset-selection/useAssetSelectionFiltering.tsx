import {useMemo} from 'react';
import {FilterableAssetDefinition} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {COMMON_COLLATOR} from '../app/Util';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';

export const useAssetSelectionFiltering = <
  T extends {
    id: string;
    key: {path: Array<string>};
    definition?: FilterableAssetDefinition | null;
  },
>({
  loading: assetsLoading,
  assetSelection,
  assets,
  useWorker = true,
}: {
  loading?: boolean;
  assetSelection: string;

  assets: T[] | undefined;
  useWorker?: boolean;
}) => {
  const assetsByKey = useMemo(
    () => Object.fromEntries((assets ?? []).map((asset) => [tokenForAssetKey(asset.key), asset])),
    [assets],
  );

  const assetsByKeyStringified = useMemo(() => JSON.stringify(assetsByKey), [assetsByKey]);
  const {loading, graphQueryItems, graphAssetKeys} = useAssetGraphData(
    assetSelection,
    useMemo(
      () => ({
        hideEdgesToNodesOutsideQuery: true,
        hideNodesMatching: (node: AssetNodeForGraphQueryFragment) => {
          return !assetsByKey[tokenForAssetKey(node.assetKey)];
        },
        loading: !!assetsLoading,
        useWorker,
      }),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [assetsByKeyStringified, assetsLoading, useWorker],
    ),
  );

  const filtered = useMemo(() => {
    return (
      graphAssetKeys
        .map((key) => {
          return assetsByKey[tokenForAssetKey(key)]!;
        })
        .filter((a) => a)
        .sort((a, b) => COMMON_COLLATOR.compare(a.key.path.join(''), b.key.path.join(''))) ?? []
    );
  }, [graphAssetKeys, assetsByKey]);

  const filteredByKey = useMemo(
    () => Object.fromEntries(filtered.map((asset) => [tokenForAssetKey(asset.key), asset])),
    [filtered],
  );

  return {filtered, filteredByKey, loading, graphAssetKeys, graphQueryItems};
};
