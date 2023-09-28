import {GraphNode} from '../Utils';

export type FolderNodeNonAssetType =
  | {groupName: string; id: string; level: number}
  | {locationName: string; id: string; level: number};

export type FolderNodeType = FolderNodeNonAssetType | {path: string; id: string; level: number};

export type TreeNodeType = {level: number; id: string; path: string};

export function nodeId(node: {path: string; id: string} | {id: string}) {
  return 'path' in node ? node.path : node.id;
}

export function getDisplayName(node: GraphNode) {
  return node.assetKey.path[node.assetKey.path.length - 1]!;
}
