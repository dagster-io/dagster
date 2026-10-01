import {GraphNode, tokenForAssetKey} from '../Utils';

export type SidebarSearchValue = {
  // The graph id of the asset, which is what selectNode expects.
  value: string;
  // The leaf segment of the asset key — the same text the sidebar row renders.
  label: string;
  // The full asset key, so a query can match on the namespace as well as the
  // displayed label. Also serves as a stable identity, which `label` is not.
  path: string;
  // The key with the leaf segment removed, shown next to the label to tell
  // apart assets that share one. Empty for single-segment keys.
  namespace: string;
};

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

// The search box offers exactly the assets the sidebar tree was built from, so
// choosing a result always lands on a row that is actually present. It used to
// be handed every asset key in the workspace, which meant a query could surface
// assets outside the current selection and picking one would silently rewrite
// the explorer's query to go fetch them.
export function buildSidebarSearchValues(nodes: {
  [assetId: string]: GraphNode;
}): SidebarSearchValue[] {
  return Object.values(nodes)
    .map((node) => {
      const {path} = node.assetKey;
      return {
        value: node.id,
        label: path[path.length - 1] ?? '',
        path: tokenForAssetKey(node.assetKey),
        namespace: path.length > 1 ? tokenForAssetKey({path: path.slice(0, -1)}) : '',
      };
    })
    .sort((a, b) => COLLATOR.compare(a.label, b.label) || COLLATOR.compare(a.path, b.path));
}
