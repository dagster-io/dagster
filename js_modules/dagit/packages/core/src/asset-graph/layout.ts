import * as dagre from 'dagre';
import groupBy from 'lodash/groupBy';

import {IBounds, IPoint} from '../graph/common';

import {GraphData, GraphNode, GraphId, displayNameForAssetKey} from './Utils';

export interface AssetLayout {
  id: GraphId;
  bounds: IBounds; // Overall frame of the box relative to 0,0 on the graph
}

export interface GroupLayout {
  id: GraphId;
  groupName: string;
  repositoryName: string;
  repositoryLocationName: string;
  repositoryDisambiguationRequired: boolean;
  bounds: IBounds; // Overall frame of the box relative to 0,0 on the graph
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
  groups: {[name: string]: GroupLayout};
};

const opts: {margin: number; mini: boolean} = {
  margin: 100,
  mini: false,
};

// Prefix group nodes in the Dagre layout so that an asset and an asset
// group cannot have the same name.
const GROUP_NODE_PREFIX = 'group__';

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

  const parentNodeIdForNode = (node: GraphNode) =>
    [
      GROUP_NODE_PREFIX,
      node.definition.repository.location.name,
      node.definition.repository.name,
      node.definition.groupName,
    ].join('__');

  const shouldRender = (node?: GraphNode) => node && node.definition.opNames.length > 0;
  const renderedNodes = Object.values(graphData.nodes).filter(shouldRender);

  const groups: {[id: string]: GroupLayout} = {};
  for (const node of renderedNodes) {
    if (node.definition.groupName) {
      const id = parentNodeIdForNode(node);
      groups[id] = {
        id,
        groupName: node.definition.groupName,
        repositoryName: node.definition.repository.name,
        repositoryLocationName: node.definition.repository.location.name,
        repositoryDisambiguationRequired: false,
        bounds: {x: 0, y: 0, width: 0, height: 0},
      };
    }
  }

  // Add all the group boxes to the graph
  const showGroups = Object.keys(groups).length > 1;
  if (showGroups) {
    Object.keys(groups).forEach((groupId) => g.setNode(groupId, {}));
  }

  // Add all the nodes to the graph
  renderedNodes.forEach((node) => {
    const {width, height} = getAssetNodeDimensions(node.definition);
    g.setNode(node.id, {width: opts.mini ? 230 : width, height});
    if (showGroups && node.definition.groupName) {
      g.setParent(node.id, parentNodeIdForNode(node));
    }
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

  let maxWidth = 0;
  let maxHeight = 0;

  const nodes: {[id: string]: AssetLayout} = {};

  g.nodes().forEach((id) => {
    const dagreNode = g.node(id);
    if (!dagreNode) {
      return;
    }
    const bounds = {
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
      width: dagreNode.width,
      height: dagreNode.height,
    };
    if (!id.startsWith(GROUP_NODE_PREFIX)) {
      nodes[id] = {id, bounds};
    }

    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  // Apply bounds to the groups based on the nodes inside them
  if (showGroups) {
    for (const node of renderedNodes) {
      if (node.definition.groupName) {
        const groupId = parentNodeIdForNode(node);
        groups[groupId].bounds =
          groups[groupId].bounds.width === 0
            ? nodes[node.id].bounds
            : extendBounds(groups[groupId].bounds, nodes[node.id].bounds);
      }
    }
    for (const group of Object.values(groups)) {
      group.bounds = padBounds(group.bounds, {x: 15, top: 80, bottom: 15});
    }
  }

  // Annotate groups that require disambiguation (same group name appears twice)
  Object.values(groupBy(Object.values(groups), (g) => g.groupName))
    .filter((set) => set.length > 1)
    .flat()
    .forEach((group) => {
      group.bounds.y -= 18;
      group.bounds.height += 18;
      group.repositoryDisambiguationRequired = true;
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
    groups: showGroups ? groups : {},
  };
};

export const getForeignNodeDimensions = (id: string) => {
  const path = JSON.parse(id);
  return {width: displayNameForAssetKey({path}).length * 8 + 30, height: 30};
};

export const padBounds = (a: IBounds, padding: {x: number; top: number; bottom: number}) => {
  return {
    x: a.x - padding.x,
    y: a.y - padding.top,
    width: a.width + padding.x * 2,
    height: a.height + padding.top + padding.bottom,
  };
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
  graphName: string | null;
  description?: string | null;
}) => {
  let height = 100;
  if (def.description) {
    height += 25;
  }
  const computeName = def.graphName || def.opNames[0] || null;
  const displayName = def.assetKey.path[def.assetKey.path.length - 1];

  if (computeName && displayName !== computeName) {
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
