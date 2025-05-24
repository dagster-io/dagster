import {GraphQueryItem} from '../app/GraphQueryImpl';
import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';

export type AssetNode = AssetNodeForGraphQueryFragment;
export type AssetGraphQueryItem = GraphQueryItem & {
  node: AssetNode;
};
