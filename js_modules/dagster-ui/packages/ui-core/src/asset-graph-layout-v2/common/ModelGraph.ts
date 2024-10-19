import {Edge} from './types';
import type {AssetNodeForGraphQueryFragment} from '../../asset-graph/types/useAssetGraphData.types';

/**
 * A model graph to be visualized.
 *
 * This is the internal format used by the visualizer. It is processed from an
 * input `Graph` (see `input_graph.ts`).
 */
export declare interface ModelGraph {
  /**
   * The id of the graph.
   *
   * It is the same as the corresponding input `Graph`.
   */
  id: string;

  /** All nodes in the model graph. */
  nodes: ModelNode[];

  /** Ids of all group nodes that are artificially created. */
  artificialGroupNodeIds?: string[];

  /** All nodes in the model graph indexed by node id. */
  nodesById: Record<string, ModelNode>;

  /** The root nodes. */
  rootNodes: Array<GroupNode | AssetNode | AssetLinkNode>;

  /** From the ids of group nodes to the edges of their subgraphs. */
  edgesByGroupNodeIds: {[id: string]: ModelEdge[]};

  /**
   * A map from the id of a group to the edges of its
   * children nodes (fromId -> targetNodeIds).
   */
  layoutGraphEdges: Record<string, Record<string, Record<string, boolean>>>;
}

/** Node tyoes in a model graph. */
export enum NodeType {
  ASSET_NODE = 'asset_node',
  ASSET_LINK_NODE = 'asset_link_node',
  GROUP_NODE = 'group_node',
}

/** The base interface of a node in model graph. */
export declare interface ModelNodeBase {
  nodeType: NodeType;

  namespace: string;

  /** Unique ID of the node */
  id: string;

  /** Id of the parent node */
  parentId?: string;

  /**
   * The level of the node in the hierarchy.
   */
  level: number;

  /** The width of the node. */
  width?: number;

  /** The height of the node. */
  height?: number;

  /**
   * The local position (x) of the node. This is relative to its parent.
   */
  x?: number;

  /**
   * The local position (y) of the node. This is relative to its parent.
   */
  y?: number;

  /**
   * Local offset (x), in order to accommodate the situations where:
   * - Subgraphs that are smaller than its parent.
   * - Edges going out of the bonding box of all the nodes.
   */
  localOffsetX?: number;
  /**
   * Local offset (y), in order to accommodate the situations where:
   * - The ns parent node has attrs table shown.
   */
  localOffsetY?: number;

  /**
   * The global position (x) of the node, relative to the svg element.
   */
  globalX?: number;

  /** The global position (y) of the node, relative to the svg element. */
  globalY?: number;
}

/** An operation node in a model graph.  */
export declare interface AssetNode extends ModelNodeBase {
  nodeType: NodeType.ASSET_NODE;

  definition: AssetNodeForGraphQueryFragment;

  /** Incoming edges. */
  upstreamEdges?: Edge[];

  /**
   * Outgoing edges.
   *
   * We populate edges for both direction for convenience.
   */
  downstreamEdges?: Edge[];

  width: number;
  height: number;
}

export declare interface AssetLinkNode extends ModelNodeBase {
  nodeType: NodeType.ASSET_LINK_NODE;

  /** Incoming edges. */
  upstreamEdges?: Edge[];

  /**
   * Outgoing edges.
   *
   * We populate edges for both direction for convenience.
   */
  downstreamEdges?: Edge[];

  width: number;
  height: number;
}

/**
 * A group node that groups op nodes and other group nodes.
 *
 * Grouping happens on namespace level. A group node will be created for each
 * unique namespace.
 */
export declare interface GroupNode extends ModelNodeBase {
  nodeType: NodeType.GROUP_NODE;

  groupName: string;
  repositoryName: string;
  repositoryLocationName: string;

  /** Its children nodes under its namespace. */
  childrenIds?: string[];

  /** All descendant nodes under this group. */
  descendantsNodeIds?: string[];

  /** All descendant asset nodes under this group. */
  descendantsAssetNodeIds?: string[];

  /** All descendant group nodes under this group. */
  descendantsGroupNodeIds?: string[];

  /** Whether this node is expanded (true) or collapsed (false). */
  expanded: boolean;

  /**
   * Whether this group node serves as a section container to reduce number of
   * nodes to layout.
   */
  sectionContainer?: boolean;
}

/** A node in a model graph. */
export type ModelNode = AssetNode | GroupNode | AssetLinkNode;

/** An edge in a model graph, */
export declare interface ModelEdge {
  id: string;
  fromId: string;
  toId: string;
  to: {x: number; y: number};
  from: {x: number; y: number};
}
