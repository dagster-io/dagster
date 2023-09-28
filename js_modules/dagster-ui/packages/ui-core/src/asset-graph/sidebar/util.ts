import {GraphNode} from '../Utils';

export function nodeId(node: {path: string; id: string} | {id: string}) {
  return 'path' in node ? node.path : node.id;
}

export function getDisplayName(node: GraphNode) {
  return node.assetKey.path[node.assetKey.path.length - 1]!;
}
