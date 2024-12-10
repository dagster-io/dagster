import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {AssetGraphFetchScope, AssetGraphQueryItem} from './useAssetGraphData';

export type ComputeGraphDataMessageType = {
  id: number;
  type: 'computeGraphData';
  repoFilteredNodes?: AssetNodeForGraphQueryFragment[];
  graphQueryItems?: AssetGraphQueryItem[];
  opsQuery: string;
  kinds: AssetGraphFetchScope['kinds'];
  hideEdgesToNodesOutsideQuery?: boolean;
  flagAssetSelectionSyntax?: boolean;
};
