import invariant from 'invariant';
import {useMemo} from 'react';

import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {HierarchicalSidebar} from '../../ui/Sidebar/HierarchicalSidebar';
import {buildHierarchyFromPaths} from '../../ui/Sidebar/buildHierarchyFromPaths';
import {HierarchyNode} from '../../ui/Sidebar/types';
import {useAllAssets} from '../useAllAssets';

export const AssetCatalogTableSidebar = ({
  selection,
  onChangeSelection,
}: {
  selection: string;
  onChangeSelection: (str: string) => void;
}) => {
  const assetSelectionWihoutKeyClause = useMemo(
    () => selectionWithoutKeyPrefix(selection),
    [selection],
  );
  const all = useAllAssets();
  const {loading, filtered} = useAssetSelectionFiltering({
    assetSelection: assetSelectionWihoutKeyClause,
    assets: all.assets,
    loading: all.loading,
  });

  const hierarchyData = useMemo(() => {
    const hierarchy = buildHierarchyFromPaths(
      (filtered || []).map((a) => tokenForAssetKey(a.key)),
      false,
    );
    const root: HierarchyNode = {
      type: 'folder',
      name: `Catalog${assetSelectionWihoutKeyClause ? ` (${assetSelectionWihoutKeyClause})` : ''}`,
      children: hierarchy,
      path: 'Catalog',
      icon: 'catalog_book',
    };
    return [root];
  }, [filtered, assetSelectionWihoutKeyClause]);

  const currentKeyPrefix = extractKeyPrefixFromSelection(selection);
  return (
    <HierarchicalSidebar
      loading={loading}
      hierarchyData={hierarchyData}
      selectedPaths={
        !currentKeyPrefix?.key ? ['Catalog'] : currentKeyPrefix?.key ? [currentKeyPrefix.key] : []
      }
      onSelectPath={(e, path) => {
        onChangeSelection(selectionReplacingKeyPrefix(selection, path));
      }}
    />
  );
};

/** Given `code_location:"dagster_open_platform"+ AND key:"aws/prod/*"`,
 * returns `aws/prod`. Returns null if there are multiple key prefixes.
 */
export function extractKeyPrefixFromSelection(selection: string) {
  const matches = Array.from(selection.matchAll(/(?<=^|\s)key:\"([^"]*\/?\*)\"/g));
  const first = matches[0];
  if (!first || matches.length !== 1) {
    return null;
  }
  invariant(first[1], 'Regexp match must contain first match group');
  return {text: first[0], key: first[1].replace(/\/\*$/, '')};
}

/* Given an existing search selection, update the existing key prefix clause or add
 * a new one. Makes an attempt to preserve logical correctness by adding parens if necessary.
 */
export function selectionReplacingKeyPrefix(selection: string, nextKeyPrefix: string): string {
  const existing = extractKeyPrefixFromSelection(selection);
  const term = nextKeyPrefix.length ? `key:"${nextKeyPrefix}/*"` : 'key:"*"';
  if (existing !== null) {
    return selection.replace(existing.text, term);
  }
  if (selection.toLowerCase().includes(' or ') && !selection.startsWith('(')) {
    return `(${selection}) AND ${term}`;
  }
  return `${selection}${selection.length > 0 ? ' AND ' : ''}${term}`;
}

/* Given an existing search selection, replace any key:"foo/*" style clause with an empty one
 * and remove it entirely if it matches the style we add.
 */
export function selectionWithoutKeyPrefix(selection: string) {
  return selectionReplacingKeyPrefix(selection, '').replace(/( AND )?key:"\*"/g, '');
}
