import * as dagre from 'dagre';

import {GraphData, GraphNode, GraphId, displayNameForAssetKey} from './Utils';

interface AssetLayout {
  id: GraphId;
  x: number;
  y: number;
  width: number;
  height: number;
}
interface IPoint {
  x: number;
  y: number;
}
export type AssetLayoutEdge = {
  from: IPoint;
  to: IPoint;
  dashed: boolean;
};

export type AssetGraphLayout = {
  width: number;
  height: number;
  edges: AssetLayoutEdge[];
  nodes: AssetLayout[];
};

const opts: {margin: number; mini: boolean} = {
  margin: 100,
  mini: false,
};

export const layoutAssetGraph = (graphData: GraphData): AssetGraphLayout => {
  const g = new dagre.graphlib.Graph();

  g.setGraph({
    rankdir: 'TB',
    marginx: opts.margin,
    marginy: opts.margin,
    nodesep: opts.mini ? 20 : 50,
    edgesep: opts.mini ? 10 : 10,
    ranksep: opts.mini ? 20 : 50,
  });
  g.setDefaultEdgeLabel(() => ({}));

  const shouldRender = (node?: GraphNode) => node && node.definition.opName;

  Object.values(graphData.nodes)
    .filter(shouldRender)
    .forEach((node) => {
      const {width, height} = getAssetNodeDimensions(node.definition);
      g.setNode(node.id, {width: opts.mini ? 230 : width, height});
    });

  const foreignNodes = {};
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
  const nodes: AssetLayout[] = [];
  Object.keys(dagreNodesById).forEach((id) => {
    const dagreNode = dagreNodesById[id];
    nodes.push({
      id,
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
      width: dagreNode.width,
      height: dagreNode.height,
    });
    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  const edges: AssetLayoutEdge[] = [];
  g.edges().forEach((e) => {
    const points = g.edge(e).points;
    edges.push({
      from: points[0],
      to: points[points.length - 1],
      dashed: false,
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

export const getAssetNodeDimensions = (def: {
  assetKey: {path: string[]};
  opName: string | null;
  description?: string | null;
}) => {
  let height = 95;
  if (def.description) {
    height += 25;
  }
  const displayName = displayNameForAssetKey(def.assetKey);
  if (def.opName && displayName !== def.opName) {
    height += 25;
  }
  return {width: Math.max(250, displayName.length * 8.0) + 25, height};
};
