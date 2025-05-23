import {useMemo} from 'react';

import {getAssetsByKey} from './util';
import {COMMON_COLLATOR} from '../app/Util';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {AssetNode} from '../graphql/types';
import {hashObject} from '../util/hashObject';
import {weakMapMemoize} from '../util/weakMapMemoize';

type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

export type FilterableAssetDefinition = Nullable<
  Partial<
    Pick<AssetNode, 'changedReasons' | 'owners' | 'groupName' | 'tags' | 'kinds'> & {
      repository: Pick<AssetNode['repository'], 'name'> & {
        location: Pick<AssetNode['repository']['location'], 'name'>;
      };
    }
  >
>;

const EMPTY_ARRAY: any[] = [];

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
  includeExternalAssets = true,
}: {
  loading?: boolean;
  assetSelection: string;

  assets: T[] | undefined;
  useWorker?: boolean;
  includeExternalAssets?: boolean;
}) => {
  const assetsByKey = getAssetsByKey(assets ?? EMPTY_ARRAY);

  const externalAssets = useMemo(
    () => (includeExternalAssets ? getExternalAssets(assets ?? EMPTY_ARRAY) : undefined),
    [assets, includeExternalAssets],
  );

  // Use a hash of the assetsByKey object to avoid re-rendering the asset graph when the assetsByKey object is updated but the keys are the same
  const assetsByKeyHash = useMemo(() => hashObject(assetsByKey), [assetsByKey]);
  const {loading, graphQueryItems, graphAssetKeys} = useAssetGraphData(
    assetSelection,
    useMemo(
      () => ({
        hideEdgesToNodesOutsideQuery: true,
        hideNodesMatching: (node: AssetNodeForGraphQueryFragment) => {
          return !assetsByKey.get(tokenForAssetKey(node.assetKey));
        },
        loading: !!assetsLoading,
        useWorker,
        externalAssets,
      }),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [assetsByKeyHash, assetsLoading, useWorker, externalAssets],
    ),
  );

  const filtered = useMemo(() => {
    return (
      graphAssetKeys
        .map((key) => {
          return assetsByKey.get(tokenForAssetKey(key))!;
        })
        .filter(Boolean)
        .sort((a, b) => COMMON_COLLATOR.compare(a.key.path.join(''), b.key.path.join(''))) ?? []
    );
  }, [graphAssetKeys, assetsByKey]);

  const filteredByKey = useMemo(
    () => Object.fromEntries(filtered.map((asset) => [tokenForAssetKey(asset.key), asset])),
    [filtered],
  );

  return {filtered, filteredByKey, loading, graphAssetKeys, graphQueryItems};
};

const getExternalAssets = weakMapMemoize(<T extends {definition?: any}>(assets: T[]) => {
  return assets.filter((asset) => !asset.definition);
});
