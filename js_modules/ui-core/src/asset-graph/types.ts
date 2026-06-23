import {GraphQueryItem} from '../app/GraphQueryImpl';
import type {WorkspaceAssetNode} from '../assets/WorkspaceAssetNode';

export type AssetNode = WorkspaceAssetNode;
export type AssetGraphQueryItem = GraphQueryItem & {
  node: AssetNode;
};
