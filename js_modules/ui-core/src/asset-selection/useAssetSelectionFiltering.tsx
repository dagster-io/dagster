import {useMemo} from 'react';

import {getAssetsByKey} from './util';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey, tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {WorkspaceAssetNode} from '../assets/useAllAssets';
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

  const {loading, graphQueryItems, graphAssetKeys} = useAssetGraphData(
    assetSelection,
    useMemo(
      () => ({
        hideEdgesToNodesOutsideQuery: true,
        hideNodesMatching: getHideNodesNotIn(assetsByKey),
        loading: !!assetsLoading,
        externalAssets,
        skip,
      }),
      [assetsByKey, assetsLoading, externalAssets, skip],
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

// Memoized so every hook instance filtering the same assets passes the same predicate.
const getHideNodesNotIn = weakMapMemoize(
  (assetsByKey: Map<string, unknown>) => (node: WorkspaceAssetNode) =>
    !assetsByKey.has(tokenForAssetKey(node.assetKey)),
);

const getExternalAssets = weakMapMemoize(<T extends {definition?: any}>(assets: T[]) => {
  return assets.filter((asset) => !asset.definition);
});
