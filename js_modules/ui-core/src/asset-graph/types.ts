import {GraphQueryItem} from '../app/GraphQueryImpl';
import {WorkspaceAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

export type AssetNode = WorkspaceAssetFragment;
export type AssetGraphQueryItem = GraphQueryItem & {
  node: AssetNode;
};
