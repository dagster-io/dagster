import * as dagre from 'dagre';
import groupBy from 'lodash/groupBy';

import {IBounds, IPoint} from '../graph/common';

import {GraphData, GraphNode, GraphId} from './Utils';

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

const opts: {margin: number} = {
  margin: 100,
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
    nodesep: 40,
    edgesep: 10,
    ranksep: 10,
  });
  g.setDefaultEdgeLabel(() => ({}));

  const parentNodeIdForNode = (node: GraphNode) =>
    [
      GROUP_NODE_PREFIX,
      node.definition.repository.location.name,
      node.definition.repository.name,
      node.definition.groupName,
    ].join('__');

  // const shouldRender = (node?: GraphNode) => node && node.definition.opNames.length > 0;
  const shouldRender = (node?: GraphNode) => node;
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
    g.setNode(node.id, getAssetNodeDimensions(node.definition));
    if (showGroups && node.definition.groupName) {
      g.setParent(node.id, parentNodeIdForNode(node));
    }
  });

  const linksToAssetsOutsideGraphedSet: {[id: string]: true} = {};

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
        (linksToAssetsOutsideGraphedSet as any)[downstreamId] = true;
      } else if (!shouldRender(graphData.nodes[upstreamId])) {
        (linksToAssetsOutsideGraphedSet as any)[upstreamId] = true;
      }
    });
  });

  // Add all the link nodes to the graph
  Object.keys(linksToAssetsOutsideGraphedSet).forEach((id) => {
    g.setNode(id, getAssetLinkDimensions());
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
      group.bounds = padBounds(group.bounds, {x: 15, top: 70, bottom: -10});
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
    const v = g.node(e.v);
    const vXInset = !!linksToAssetsOutsideGraphedSet[e.v] ? 16 : 24;
    const w = g.node(e.w);
    const wXInset = !!linksToAssetsOutsideGraphedSet[e.w] ? 16 : 24;

    // Ignore the coordinates from dagre and use the top left + bottom left of the
    edges.push({
      from: {x: v.x - v.width / 2 + vXInset, y: v.y - 30 + v.height / 2},
      fromId: e.v,
      to: {x: w.x - w.width / 2 + wXInset, y: w.y + 20 - w.height / 2},
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

export const ASSET_LINK_NAME_MAX_LENGTH = 10;

export const getAssetLinkDimensions = () => {
  return {width: 106, height: 90};
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

export const ASSET_NODE_NAME_MAX_LENGTH = 28;

export const getAssetNodeDimensions = (def: {
  assetKey: {path: string[]};
  opNames: string[];
  isSource: boolean;
  isObservable: boolean;
  isPartitioned: boolean;
  graphName: string | null;
  description?: string | null;
  computeKind: string | null;
}) => {
  const width = 265;

  if (def.isSource && !def.isObservable) {
    return {width, height: 102};
  } else {
    let height = 100; // top tags area + name + description

    if (def.isPartitioned) {
      height += 40;
    }
    if (def.isSource) {
      height += 30; // observed
    } else {
      height += 26; // status row
    }

    height += 30; // tag

    return {width, height};
  }
};
