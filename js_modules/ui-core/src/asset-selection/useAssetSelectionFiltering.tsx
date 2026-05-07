import {useMemo} from 'react';

import {getAssetsByKey} from './util';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {WorkspaceAssetNode} from '../assets/useAllAssets';
import {hashObject} from '../util/hashObject';
import {weakMapMemoize} from '../util/weakMapMemoize';

type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

export type FilterableAssetDefinition = Nullable<
  Partial<
    Pick<WorkspaceAssetNode, 'changedReasons' | 'owners' | 'groupName' | 'tags' | 'kinds'> & {
      repository: Pick<WorkspaceAssetNode['repository'], 'name'> & {
        location: Pick<WorkspaceAssetNode['repository']['location'], 'name'>;
      };
    }
  >
>;

const EMPTY_ARRAY: never[] = [];

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
  includeExternalAssets = true,
  skip = false,
}: {
  loading?: boolean;
  assetSelection: string;
  assets: T[] | undefined;
  includeExternalAssets?: boolean;
  skip?: boolean;
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
        hideNodesMatching: (node: WorkspaceAssetNode) => {
          return !assetsByKey.get(tokenForAssetKey(node.assetKey));
        },
        loading: !!assetsLoading,
        externalAssets,
        skip,
      }),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [assetsByKeyHash, assetsLoading, externalAssets, skip],
    ),
  );

  const filtered = useMemo(() => {
    return (
      graphAssetKeys
        .map((key) => {
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          return assetsByKey.get(tokenForAssetKey(key))!;
        })
        .filter(Boolean)
        .sort((a, b) =>
          COMMON_COLLATOR.compare(displayNameForAssetKey(a.key), displayNameForAssetKey(b.key)),
        ) ?? []
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
