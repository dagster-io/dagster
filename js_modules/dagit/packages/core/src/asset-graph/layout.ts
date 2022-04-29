import * as dagre from 'dagre';
import uniq from 'lodash/uniq';

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

  bundleEdges: AssetLayoutEdge[];
  bundles: {[id: string]: AssetLayout};
};

const opts: {margin: number; mini: boolean} = {
  margin: 100,
  mini: false,
};

function identifyBundles(nodeIds: string[]) {
  const pathPrefixes: {[prefixId: string]: string[]} = {};

  for (const nodeId of nodeIds) {
    const assetKeyPath = JSON.parse(nodeId);

    for (let ii = 1; ii < assetKeyPath.length; ii++) {
      const prefix = assetKeyPath.slice(0, ii);
      const key = JSON.stringify(prefix);
      pathPrefixes[key] = pathPrefixes[key] || [];
      pathPrefixes[key].push(nodeId);
    }
  }

  for (const key of Object.keys(pathPrefixes)) {
    if (pathPrefixes[key].length <= 1) {
      delete pathPrefixes[key];
    }
  }

  const finalBundlePrefixes: {[prefixId: string]: string[]} = {};
  const finalBundleIdForNodeId: {[id: string]: string} = {};

  // Sort the prefix keys by length descending and iterate from the deepest folders first.
  // Dedupe asset keys and replace asset keys we've already seen with the (deeper) folder
  // they are within. This gets us "multi layer folders" of nodes.

  // Turn this:
  // {
  //  "s3": [["s3", "collect"], ["s3", "prod", "a"], ["s3", "prod", "b"]],
  //  "s3/prod": ["s3", "prod", "a"], ["s3", "prod", "b"]
  // }

  // Into this:
  // {
  //  "s3/prod": ["s3", "prod", "a"], ["s3", "prod", "b"]
  //  "s3": [["s3", "collect"], ["s3", "prod"]],
  // }

  for (const prefixId of Object.keys(pathPrefixes).sort((a, b) => b.length - a.length)) {
    finalBundlePrefixes[prefixId] = uniq(
      pathPrefixes[prefixId].map((p) =>
        finalBundleIdForNodeId[p] ? finalBundleIdForNodeId[p] : p,
      ),
    );
    finalBundlePrefixes[prefixId].forEach((id) => (finalBundleIdForNodeId[id] = prefixId));
  }
  return finalBundlePrefixes;
}

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

  // Create "parent" nodes for nodes with a shared ID (path) prefix (eg: s3>a, s3>b),
  // and then place the children inside. Note that the bundles are identified in order
  // and bundleMapping can reference bundles as children - this code can create multiple
  // layers of parents!
  const bundleMapping = identifyBundles(g.nodes());
  for (const [parentId, nodeIds] of Object.entries(bundleMapping)) {
    g.setNode(parentId, {});
    for (const nodeId of nodeIds) {
      g.setParent(nodeId, parentId);
    }
  }

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
    if (bundleMapping[id]) {
      return;
    }
    nodes[id] = {id, bounds};

    // If this node was inside one or more parent nodes, upsert the parent box
    // into the bundles result set and expand it to include the child. Note:
    // dagre does give us "parent" node dimensions, but sometimes they're randomly
    // much larger than the contents.
    let bundleId = g.parent(id);
    while (bundleId) {
      bundles[bundleId] = bundles[bundleId] || {id: bundleId, bounds};
      bundles[bundleId].bounds = extendBounds(bundles[bundleId].bounds, {
        x: bounds.x - opts.margin / 4,
        y: bounds.y - opts.margin / 4,
        width: bounds.width + opts.margin / 2,
        height: bounds.height + opts.margin / 2,
      });
      bundleId = g.parent(bundleId);
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
        fromId: e.v,
        to: points[points.length - 1],
        toId: e.w,
      });
    } else {
      edges.push({
        from: points[0],
        fromId: e.v,
        to: points[points.length - 1],
        toId: e.w,
      });
    }
  });

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

export const extendBounds = (a: IBounds, b: IBounds) => {
  const xmin = Math.min(a.x, b.x);
  const ymin = Math.min(a.y, b.y);
  const xmax = Math.max(a.x + a.width, b.x + b.width);
  const ymax = Math.max(a.y + a.height, b.y + b.height);
  return {x: xmin, y: ymin, width: xmax - xmin, height: ymax - ymin};
};

export const ASSET_NODE_ANNOTATIONS_MAX_WIDTH = 65;
export const ASSET_NODE_NAME_MAX_LENGTH = 32;
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
