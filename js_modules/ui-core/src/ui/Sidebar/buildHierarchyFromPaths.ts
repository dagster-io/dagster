import {HierarchyNode, TreeNode} from './types';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export function buildHierarchyFromPaths(paths: string[], includeFiles: boolean): HierarchyNode[] {
  // Note: This is a clever use of reduce that traverses down, upserting
  // nested objects for each layer of folders in the paths.
  const tree: TreeNode = {};
  paths.forEach((path) => {
    path.split('/').reduce((node, segment) => {
      node[segment] ||= {};
      return node[segment];
    }, tree);
  });

  const convert = (obj: TreeNode, prefix = ''): HierarchyNode[] =>
    Object.entries(obj)
      .map(([name, nodeValue]) => {
        const path = prefix ? `${prefix}/${name}` : name;
        if (Object.keys(nodeValue).length === 0) {
          return {type: 'file' as const, name, path};
        } else {
          return {type: 'folder' as const, name, path, children: convert(nodeValue, path)};
        }
      })
      .filter((t) => t.type === 'folder' || includeFiles)
      .sort((a, b) =>
        a.type !== b.type ? (a.type === 'folder' ? -1 : 1) : COLLATOR.compare(a.name, b.name),
      );

  return convert(tree);
}
