import * as dagre from 'dagre';

import {ASSET_NODE_WIDTH, Config, LayoutAssetGraphOptions} from '../../asset-graph/layout';
import {GroupNode, ModelEdge, ModelGraph, ModelNode, NodeType} from '../common/ModelGraph';
import {LAYOUT_MARGIN_X} from '../common/conts';
import {Point, Rect} from '../common/types';
import {isNodeExpanded} from '../common/utils';

/** The margin for the top and bottom side of the layout. */
export const LAYOUT_MARGIN_TOP = 36;

/** The margin for the bottom side of the layout */
export const LAYOUT_MARGIN_BOTTOM = 16;

/** The default height of a node. */
export const DEFAULT_NODE_HEIGHT = 26;

/** Node width for test cases. */
export const NODE_WIDTH_FOR_TEST = 50;

/** A node in dagre. */
export declare interface DagreNode {
  id: string;
  width: number;
  height: number;
  x?: number;
  y?: number;
  _node: ModelNode;
}

interface LayoutGraph {
  nodes: {[id: string]: DagreNode};
  upstreamEdges: {[fromId: string]: string[]};
  downstreamEdges: {[fromId: string]: string[]};
}

/**
 * To manage graph layout related tasks.
 *
 * TODO: distribute this task to multiple workers to improvement performance.
 */
export class GraphLayout {
  dagreGraph!: dagre.graphlib.Graph;

  constructor(
    private readonly modelGraph: ModelGraph,
    private readonly options: LayoutAssetGraphOptions = {direction: 'horizontal'},
  ) {
    this.dagreGraph = new dagre.graphlib.Graph();
  }

  /** Lays out the model graph rooted from the given root node.  */
  layout(rootNodeId?: string): Rect {
    // Get the children nodes of the given root node.
    let rootNode: GroupNode | undefined = undefined;
    let nodes: ModelNode[] = [];
    if (rootNodeId == null) {
      nodes = this.modelGraph.rootNodes;
    } else {
      rootNode = this.modelGraph.nodesById[rootNodeId] as GroupNode;
      nodes = (rootNode.childrenIds || []).map((nodeId) => this.modelGraph.nodesById[nodeId]!);
    }

    // Get layout graph.
    const layoutGraph = getLayoutGraph(rootNode?.id || '', nodes, this.modelGraph);

    const config = Object.assign(
      {},
      Config[this.options.direction],
      {ranker: 'network-simplex'},
      this.options.overrides || {},
    );

    this.dagreGraph.setGraph(config);
    this.dagreGraph.setDefaultEdgeLabel(() => ({}));
    // Set nodes/edges to dagre.
    for (const id of Object.keys(layoutGraph.nodes)) {
      const dagreNode = layoutGraph.nodes[id]!;
      this.dagreGraph.setNode(id, dagreNode);
    }
    for (const fromId of Object.keys(layoutGraph.downstreamEdges)) {
      for (const toId of layoutGraph.downstreamEdges[fromId]!) {
        this.dagreGraph.setEdge(fromId, toId, {weight: 1});
      }
    }

    // Run the layout algorithm.
    dagre.layout(this.dagreGraph);

    const {width = 0, height = 0} = this.dagreGraph.graph();

    // Set the results back to the original model nodes and calculate the bound
    // that contains all the nodes.
    let minX = Number.MAX_VALUE;
    let minY = Number.MAX_VALUE;
    let maxX = Number.NEGATIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;
    for (const node of nodes) {
      const dagreNode = layoutGraph.nodes[node.id];
      if (!dagreNode) {
        console.warn(`Node "${node.id}" is not in the dagre layout result`);
        continue;
      }
      node.x = (dagreNode.x || 0) - dagreNode.width / 2;
      node.y = (dagreNode.y || 0) - dagreNode.height / 2;
      node.width = dagreNode.width;
      node.height = dagreNode.height;
      node.localOffsetX = 0;
      node.localOffsetY = 0;

      minX = Math.min(minX, node.x);
      minY = Math.min(minY, node.y);
      maxX = Math.max(maxX, node.x + node.width);
      maxY = Math.max(maxY, node.y + node.height);
    }

    // Expand the bound to include all the edges.
    let minEdgeX = Number.MAX_VALUE;
    let minEdgeY = Number.MAX_VALUE;
    let maxEdgeX = Number.NEGATIVE_INFINITY;
    let maxEdgeY = Number.NEGATIVE_INFINITY;
    const dagreEdgeRefs = this.dagreGraph.edges();
    const edges: ModelEdge[] = [];
    for (const dagreEdge of dagreEdgeRefs) {
      const points = this.dagreGraph.edge(dagreEdge).points as Point[];
      const fromNode = this.modelGraph.nodesById[dagreEdge.v];
      const toNode = this.modelGraph.nodesById[dagreEdge.w];
      const dagreFromNode = this.dagreGraph.node(dagreEdge.v);
      const dagreToNode = this.dagreGraph.node(dagreEdge.w);
      if (fromNode == null || dagreFromNode == null) {
        console.warn(`Edge from node not found: "${dagreEdge.v}"`);
        debugger;
        continue;
      }
      if (toNode == null || dagreToNode == null) {
        console.warn(`Edge to node not found: "${dagreEdge.w}"`);
        debugger;
        continue;
      }
      const edgeId = `${fromNode.id}|${toNode.id}`;
      const fromXInset = fromNode.nodeType === NodeType.ASSET_LINK_NODE ? 16 : 24;
      const toXInset = toNode.nodeType === NodeType.ASSET_LINK_NODE ? 16 : 24;
      const {
        x: fromX = 0,
        y: fromY = 0,
        width: fromWidth = 0,
        height: fromHeight = 0,
      } = dagreFromNode;
      const {x: toX = 0, y: toY = 0, width: toWidth = 0, height: toHeight = 0} = dagreToNode;
      edges.push({
        id: edgeId,
        fromId: fromNode.id,
        toId: toNode.id,
        ...(this.options.direction === 'horizontal'
          ? {
              from: {x: fromX + fromWidth / 2, y: fromY},
              to: {x: toX - toWidth / 2 - 5, y: toY},
            }
          : {
              from: {x: fromX - fromWidth / 2 + fromXInset, y: fromY - 30 + fromHeight / 2},
              to: {x: toX - toWidth / 2 + toXInset, y: toY + 20 - toHeight / 2},
            }),
      });
      for (const point of points) {
        minEdgeX = Math.min(minEdgeX, point.x);
        minEdgeY = Math.min(minEdgeY, point.y);
        maxEdgeX = Math.max(maxEdgeX, point.x);
        maxEdgeY = Math.max(maxEdgeY, point.y);
      }
    }

    this.modelGraph.edgesByGroupNodeIds[rootNodeId || ''] = edges;

    // Offset nodes to take into account of edges going out of the bound of all
    // the nodes.
    if (minEdgeX < minX) {
      for (const node of nodes) {
        node.localOffsetX = Math.max(0, minX - minEdgeX);
        if (!isFinite(node.localOffsetX)) {
          node.localOffsetX = -width / 2;
        }
      }
    }

    minX = Math.min(minEdgeX, minX);
    maxX = Math.max(maxEdgeX, maxX);

    // Make sure the subgraph width is at least the width of the root node.
    let subgraphFullWidth = maxX - minX + LAYOUT_MARGIN_X * 2;
    if (rootNode) {
      const parentNodeWidth = ASSET_NODE_WIDTH;
      if (subgraphFullWidth < parentNodeWidth) {
        const extraOffsetX = (parentNodeWidth - subgraphFullWidth) / 2;
        for (const node of nodes) {
          if (!node.localOffsetX) {
            node.localOffsetX = 0;
          }
          node.localOffsetX += extraOffsetX;
        }
        subgraphFullWidth = parentNodeWidth;
      }
    }

    return {
      x: minX,
      y: minY,
      width: width ?? 0,
      height: height ?? 0,
    };
  }
}

/** Gets a layout graph for the given nodes. */
export function getLayoutGraph(
  rootGroupNodeId: string,
  nodes: ModelNode[],
  modelGraph: ModelGraph,
): LayoutGraph {
  const layoutGraph: LayoutGraph = {
    nodes: {},
    upstreamEdges: {},
    downstreamEdges: {},
  };

  // Create layout graph nodes.
  for (const node of nodes) {
    if (!isNodeExpanded(node.id, modelGraph)) {
      continue;
    }
    const dagreNode: DagreNode = {
      id: node.id,
      width: node.width || ASSET_NODE_WIDTH,
      height: node.height || 110,
      _node: node,
    };
    layoutGraph.nodes[node.id] = dagreNode;
  }

  // Set layout graph edges.
  const curLayoutGraphEdges = modelGraph.layoutGraphEdges[rootGroupNodeId] || {};
  for (const [fromId, toNodeIds] of Object.entries(curLayoutGraphEdges)) {
    for (const toId of Object.keys(toNodeIds)) {
      let finalToId: string | undefined = toId;
      let finalFromId: string | undefined = fromId;
      /**
       * If a node is not expanded then find the expanded ancestor node
       * and draw the edge from there instead
       */
      if (!isNodeExpanded(finalToId, modelGraph)) {
        finalToId = findExpandedAncestorNode(toId, modelGraph);
      }
      if (!isNodeExpanded(finalFromId, modelGraph)) {
        finalFromId = findExpandedAncestorNode(fromId, modelGraph);
      }
      if (
        finalFromId &&
        finalToId &&
        modelGraph.nodesById[finalFromId] &&
        modelGraph.nodesById[finalToId]
      ) {
        addLayoutGraphEdge(layoutGraph, finalFromId, finalToId);
      } else {
        debugger;
      }
    }
  }

  return layoutGraph;
}

function addLayoutGraphEdge(layoutGraph: LayoutGraph, fromId: string, toId: string) {
  if (layoutGraph.downstreamEdges[fromId] == null) {
    layoutGraph.downstreamEdges[fromId] = [];
  }
  layoutGraph.downstreamEdges[fromId]!.push(toId);

  if (layoutGraph.upstreamEdges[toId] == null) {
    layoutGraph.upstreamEdges[toId] = [];
  }
  layoutGraph.upstreamEdges[toId]!.push(fromId);
}

function findExpandedAncestorNode(id: string, modelGraph: ModelGraph) {
  const node = modelGraph.nodesById[id];
  if (node && node.parentId) {
    const parent = modelGraph.nodesById[node.parentId];
    if (parent) {
      if (isNodeExpanded(parent.id, modelGraph)) {
        return node.parentId;
      } else {
        return findExpandedAncestorNode(parent.id, modelGraph);
      }
    }
  }
  return undefined;
}
