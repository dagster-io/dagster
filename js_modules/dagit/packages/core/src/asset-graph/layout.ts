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
  to: IPoint;
  dashed: boolean;
};

export type AssetGraphLayout = {
  width: number;
  height: number;
  edges: AssetLayoutEdge[];
  nodes: {[id: string]: AssetLayout};

  bundleEdges: AssetLayoutEdge[];
  bundles: {[id: string]: AssetLayout};
};

const opts: {margin: number; mini: boolean} = {
  margin: 100,
  mini: false,
};

const BUNDLE_SEED: {[key: string]: string[]} = {
  '["stats"]': ['["story_daily_stats"]', '["comment_daily_stats"]', '["activity_daily_stats"]'],
  '["download"]': ['["id_range_for_time"]', '["items"]', '["comments"]', '["stories"]'],
  '["recommender"]': [
    '["comment_stories"]',
    '["user_story_matrix"]',
    '["recommender_model"]',
    '["comment_top_stories"]',
    '["user_top_recommended_stories"]',
  ],
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

  const shouldRender = (node?: GraphNode) => node && node.definition.opName;

  Object.values(graphData.nodes)
    .filter(shouldRender)
    .forEach((node) => {
      const {width, height} = getAssetNodeDimensions(node.definition);
      g.setNode(node.id, {width: opts.mini ? 230 : width, height});
    });

  const foreignNodes = {};

  for (const [parent, children] of Object.entries(BUNDLE_SEED)) {
    g.setNode(parent, {});
    for (const child of children) {
      g.setParent(child, parent);
    }
  }

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
      // const upstreamParentId = g.parent(upstreamId);
      // const downstreamParentId = g.parent(downstreamId);
      // if (upstreamParentId || downstreamParentId) {
      //   g.setEdge(
      //     {v: upstreamParentId || upstreamId, w: downstreamParentId || downstreamId},
      //     {weight: 1},
      //   );
      // }

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

  const nodes: {[id: string]: AssetLayout} = {};
  const bundles: {[id: string]: AssetLayout} = {};

  Object.keys(dagreNodesById).forEach((id) => {
    const dagreNode = dagreNodesById[id];
    const bounds = {
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
      width: dagreNode.width,
      height: dagreNode.height,
    };
    if (BUNDLE_SEED[id]) {
      bundles[id] = {id, bounds};
    } else {
      nodes[id] = {id, bounds};
    }
    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  const edges: AssetLayoutEdge[] = [];
  const bundleEdges: AssetLayoutEdge[] = [];

  g.edges().forEach((e) => {
    const points = g.edge(e).points;
    if (bundles[e.v] || bundles[e.w]) {
      bundleEdges.push({
        from: points[0],
        to: points[points.length - 1],
        dashed: false,
      });
    } else {
      edges.push({
        from: points[0],
        to: points[points.length - 1],
        dashed: false,
      });
    }
  });

  console.log(bundles);
  return {
    nodes,
    edges,
    bundles,
    bundleEdges,
    width: maxWidth + opts.margin,
    height: maxHeight + opts.margin,
  };
};

export const getForeignNodeDimensions = (id: string) => {
  const path = JSON.parse(id);
  return {width: displayNameForAssetKey({path}).length * 8 + 30, height: 30};
};

export const ASSET_NODE_ANNOTATIONS_MAX_WIDTH = 65;
export const ASSET_NODE_NAME_MAX_LENGTH = 50;
const DISPLAY_NAME_PX_PER_CHAR = 8.0;

export const getAssetNodeDimensions = (def: {
  assetKey: {path: string[]};
  opName: string | null;
  description?: string | null;
}) => {
  let height = 75;
  if (def.description) {
    height += 25;
  }
  const displayName = displayNameForAssetKey(def.assetKey);
  if (def.opName && displayName !== def.opName) {
    height += 25;
  }
  return {
    width:
      Math.max(
        200,
        Math.min(ASSET_NODE_NAME_MAX_LENGTH, displayName.length) * DISPLAY_NAME_PX_PER_CHAR,
      ) + ASSET_NODE_ANNOTATIONS_MAX_WIDTH,
    height,
  };
};
