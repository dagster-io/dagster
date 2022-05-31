import * as dagre from 'dagre';

import {IBounds, IPoint} from '../graph/common';

import {GraphData, GraphNode, GraphId, displayNameForAssetKey} from './Utils';

export interface AssetLayout {
  id: GraphId;

  // Overall frame of the box relative to 0,0 on the graph
  bounds: IBounds;
}

export type AssetLayoutEdge = {
  from: IPoint;
  fromId: string;
  to: IPoint;
  toId: string;
};

export type AssetGraphLayout = {
  width: number;
  height: number;
  edges: AssetLayoutEdge[];
  nodes: {[id: string]: AssetLayout};
};

const opts: {margin: number; mini: boolean} = {
  margin: 100,
  mini: false,
};

export const layoutAssetGraph = (graphData: GraphData): AssetGraphLayout => {
  const g = new dagre.graphlib.Graph({compound: true});

  g.setGraph({
    rankdir: 'TB',
    marginx: opts.margin,
    marginy: opts.margin,
    nodesep: opts.mini ? 20 : 50,
    edgesep: opts.mini ? 10 : 10,
    ranksep: opts.mini ? 20 : 50,
  });
  g.setDefaultEdgeLabel(() => ({}));

  const shouldRender = (node?: GraphNode) => node && node.definition.opNames.length > 0;

  // Add all the nodes to the graph
  Object.values(graphData.nodes)
    .filter(shouldRender)
    .forEach((node) => {
      const {width, height} = getAssetNodeDimensions(node.definition);
      g.setNode(node.id, {width: opts.mini ? 230 : width, height});
    });

  const foreignNodes = {};

  // Add the edges to the graph, and accumulate a set of "foreign nodes" (for which
  // we have an inbound/outbound edge, but we don't have the `node` in the graphData).
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);
    downstreamIds.forEach((downstreamId) => {
      if (
        !shouldRender(graphData.nodes[downstreamId]) &&
        !shouldRender(graphData.nodes[upstreamId])
      ) {
        return;
      }

      g.setEdge({v: upstreamId, w: downstreamId}, {weight: 1});

      if (!shouldRender(graphData.nodes[downstreamId])) {
        foreignNodes[downstreamId] = true;
      } else if (!shouldRender(graphData.nodes[upstreamId])) {
        foreignNodes[upstreamId] = true;
      }
    });
  });

  // Add all the foreign nodes to the graph
  Object.keys(foreignNodes).forEach((id) => {
    g.setNode(id, getForeignNodeDimensions(id));
  });

  dagre.layout(g);

  const dagreNodesById: {[id: string]: dagre.Node} = {};
  g.nodes().forEach((id) => {
    const node = g.node(id);
    if (!node) {
      return;
    }
    dagreNodesById[id] = node;
  });

  let maxWidth = 0;
  let maxHeight = 0;

  const nodes: {[id: string]: AssetLayout} = {};

  Object.keys(dagreNodesById).forEach((id) => {
    const dagreNode = dagreNodesById[id];
    const bounds = {
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
      width: dagreNode.width,
      height: dagreNode.height,
    };
    nodes[id] = {id, bounds};

    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  const edges: AssetLayoutEdge[] = [];

  g.edges().forEach((e) => {
    const points = g.edge(e).points;
    edges.push({
      from: points[0],
      fromId: e.v,
      to: points[points.length - 1],
      toId: e.w,
    });
  });

  return {
    nodes,
    edges,
    width: maxWidth + opts.margin,
    height: maxHeight + opts.margin,
  };
};

export const getForeignNodeDimensions = (id: string) => {
  const path = JSON.parse(id);
  return {width: displayNameForAssetKey({path}).length * 8 + 30, height: 30};
};

export const extendBounds = (a: IBounds, b: IBounds) => {
  const xmin = Math.min(a.x, b.x);
  const ymin = Math.min(a.y, b.y);
  const xmax = Math.max(a.x + a.width, b.x + b.width);
  const ymax = Math.max(a.y + a.height, b.y + b.height);
  return {x: xmin, y: ymin, width: xmax - xmin, height: ymax - ymin};
};

export const ASSET_NODE_ICON_WIDTH = 20;
export const ASSET_NODE_ANNOTATIONS_MAX_WIDTH = 65;
export const ASSET_NODE_NAME_MAX_LENGTH = 32;
const DISPLAY_NAME_PX_PER_CHAR = 8.0;

export const assetNameMaxlengthForWidth = (width: number) => {
  return (
    (width - ASSET_NODE_ANNOTATIONS_MAX_WIDTH - ASSET_NODE_ICON_WIDTH) / DISPLAY_NAME_PX_PER_CHAR
  );
};

export const getAssetNodeDimensions = (def: {
  assetKey: {path: string[]};
  opNames: string[];
  description?: string | null;
}) => {
  let height = 75;
  if (def.description) {
    height += 25;
  }
  const displayName = displayNameForAssetKey(def.assetKey);
  const firstOp = def.opNames[0];
  if (firstOp && displayName !== firstOp) {
    height += 25;
  }
  return {
    width:
      Math.max(
        200,
        Math.min(ASSET_NODE_NAME_MAX_LENGTH, displayName.length) * DISPLAY_NAME_PX_PER_CHAR,
      ) +
      ASSET_NODE_ICON_WIDTH +
      ASSET_NODE_ANNOTATIONS_MAX_WIDTH,
    height,
  };
};
