import {AssetKey} from '../assets/types';
import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {AssetGraphFetchScope, AssetGraphQueryItem} from './useAssetGraphData';

type BaseType = {
  id: number;
};

export type ComputeGraphDataMessageType = BaseType & {
  type: 'computeGraphData';
  repoFilteredNodes?: AssetNodeForGraphQueryFragment[];
  graphQueryItems?: AssetGraphQueryItem[];
  opsQuery: string;
  kinds: AssetGraphFetchScope['kinds'];
  hideEdgesToNodesOutsideQuery?: boolean;
  supplementaryData?: Record<string, AssetKey[]> | null;
};

export type BuildGraphDataMessageType = BaseType & {
  nodes: AssetNodeForGraphQueryFragment[];
  type: 'buildGraphData';
};

export type ComputeGraphDataWorkerMessageType =
  | ComputeGraphDataMessageType
  | BuildGraphDataMessageType;
