import {AssetGraphQueryItem} from './types';
import {AssetGraphFetchScope} from './useAssetGraphData';
import {AssetKey} from '../assets/types';
import {WorkspaceAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

type BaseType = {
  id: number;
};

export type ComputeGraphDataMessageType = BaseType & {
  type: 'computeGraphData';
  repoFilteredNodes?: WorkspaceAssetFragment[];
  graphQueryItems?: AssetGraphQueryItem[];
  opsQuery: string;
  kinds: AssetGraphFetchScope['kinds'];
  hideEdgesToNodesOutsideQuery?: boolean;
  supplementaryData?: Record<string, AssetKey[]> | null;
};

export type BuildGraphDataMessageType = BaseType & {
  nodes: WorkspaceAssetFragment[];
  type: 'buildGraphData';
};

export type ComputeGraphDataWorkerMessageType =
  | ComputeGraphDataMessageType
  | BuildGraphDataMessageType;
