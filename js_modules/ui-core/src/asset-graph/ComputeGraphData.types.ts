import {AssetGraphQueryItem} from './types';
import {AssetGraphFetchScope} from './useAssetGraphData';
import {AssetKey} from '../assets/types';
import type {WorkspaceAssetNode} from '../assets/useAllAssets';

type BaseType = {
  id: number;
};

export type ComputeGraphDataMessageType = BaseType & {
  type: 'computeGraphData';
  repoFilteredNodes?: WorkspaceAssetNode[];
  graphQueryItems?: AssetGraphQueryItem[];
  opsQuery: string;
  kinds: AssetGraphFetchScope['kinds'];
  hideEdgesToNodesOutsideQuery?: boolean;
  supplementaryData?: Record<string, AssetKey[]> | null;
};

export type BuildGraphDataMessageType = BaseType & {
  nodes: WorkspaceAssetNode[];
  type: 'buildGraphData';
};

export type ComputeGraphDataWorkerMessageType =
  | ComputeGraphDataMessageType
  | BuildGraphDataMessageType;
