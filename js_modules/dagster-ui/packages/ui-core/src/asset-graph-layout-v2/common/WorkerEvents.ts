import {ModelGraph} from './ModelGraph';
import {GraphData} from '../../asset-graph/Utils';
import {LayoutAssetGraphOptions} from '../worker/GraphConfig';

/** The base of all worker events. */
export declare interface WorkerEventBase {
  eventType: WorkerEventType;
  requestId: number;
}

/** The request for processing an input graph. */
export declare interface ProcessGraphRequest extends WorkerEventBase {
  eventType: WorkerEventType.PROCESS_GRAPH_REQ;
  graph: GraphData;
  graphId: string;
  targetDeepestGroupNodeIdsToExpand: string[];
  options: LayoutAssetGraphOptions;
}

/** The response for processing an input graph. */
export declare interface ProcessGraphResponse extends WorkerEventBase {
  eventType: WorkerEventType.PROCESS_GRAPH_RESP;
  modelGraph: ModelGraph;
  graphId: string;
}

/** The request for expanding/collapsing a group node. */
export declare interface UpdateExpandedGroupsRequest extends WorkerEventBase {
  eventType: WorkerEventType.UPDATE_EXPANDED_GROUPS_REQ;
  graphId: string;
  targetDeepestGroupNodeIdsToExpand: string[];
  options: LayoutAssetGraphOptions;
}

/** The response for expanding/collapsing a group node. */
export declare interface UpdateExpandedGroupsResponse extends WorkerEventBase {
  eventType: WorkerEventType.UPDATE_EXPANDED_GROUPS_RESP;
  modelGraph: ModelGraph;
}

/** Various worker event types. */
export enum WorkerEventType {
  PROCESS_GRAPH_REQ,
  PROCESS_GRAPH_RESP,
  UPDATE_EXPANDED_GROUPS_REQ,
  UPDATE_EXPANDED_GROUPS_RESP,
  UPDATE_PROCESSING_PROGRESS,
}

export type WorkerEvent =
  | ProcessGraphRequest
  | ProcessGraphResponse
  | UpdateExpandedGroupsRequest
  | UpdateExpandedGroupsResponse;
