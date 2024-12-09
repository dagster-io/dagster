import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {AssetGraphFetchScope, AssetGraphQueryItem} from './useAssetGraphData';

export type ComputeGraphDataMessageType = {
  type: 'computeGraphData';
  repoFilteredNodes?: AssetNodeForGraphQueryFragment[];
  graphQueryItems?: AssetGraphQueryItem[];
  opsQuery: string;
  kinds: AssetGraphFetchScope['kinds'];
  hideEdgesToNodesOutsideQuery?: boolean;
  flagAssetSelectionSyntax?: boolean;
};
