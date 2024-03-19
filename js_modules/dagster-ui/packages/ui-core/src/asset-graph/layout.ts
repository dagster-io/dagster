import * as dagre from 'dagre';

import {GraphData, GraphId, GraphNode, groupIdForNode, isGroupId} from './Utils';
import {IBounds, IPoint} from '../graph/common';
import {ChangeReason} from '../graphql/types';

export type AssetLayoutDirection = 'vertical' | 'horizontal';

export interface AssetLayout {
  id: GraphId;
  bounds: IBounds; // Overall frame of the box relative to 0,0 on the graph
}

export interface GroupLayout {
  id: GraphId;
  groupName: string;
  repositoryName: string;
  repositoryLocationName: string;
  bounds: IBounds; // Overall frame of the box relative to 0,0 on the graph
  expanded: boolean;
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
const MARGIN = 100;

export type LayoutAssetGraphConfig = dagre.GraphLabel & {
  direction: AssetLayoutDirection;
  /** Pass `auto` to use getAssetNodeDimensions, or a value to give nodes a fixed height */
  nodeHeight: number | 'auto';
  /** Our asset groups have "title bars" - use these numbers to adjust the bounding boxes.
   * Note that these adjustments are applied post-dagre layout. For padding > nodesep, you
   * may need to set "clusterpaddingtop", "clusterpaddingbottom" so Dagre lays out the boxes
   * with more spacing.
   */
  groupPaddingTop: number;
  groupPaddingBottom: number;
  groupRendering: 'if-varied' | 'always';

  /** Supported in Dagre, just not documented. Additional spacing between group nodes */
  clusterpaddingtop?: number;
  clusterpaddingbottom?: number;
};

export type LayoutAssetGraphOptions = {
  direction: AssetLayoutDirection;
  overrides?: Partial<LayoutAssetGraphConfig>;
};

export const Config = {
  horizontal: {
    ranker: 'tight-tree',
    direction: 'horizontal',
    marginx: MARGIN,
    marginy: MARGIN,
    ranksep: 60,
    rankdir: 'LR',
    edgesep: 90,
    nodesep: -10,
    nodeHeight: 'auto',
    groupPaddingTop: 65,
    groupPaddingBottom: -15,
    groupRendering: 'if-varied',
    clusterpaddingtop: 100,
  },
  vertical: {
    ranker: 'tight-tree',
    direction: 'horizontal',
    marginx: MARGIN,
    marginy: MARGIN,
    ranksep: 20,
    rankdir: 'TB',
    nodesep: 40,
    edgesep: 10,
    nodeHeight: 'auto',
    groupPaddingTop: 40,
    groupPaddingBottom: -20,
    groupRendering: 'if-varied',
  },
};

export const layoutAssetGraph = (
  graphData: GraphData,
  opts: LayoutAssetGraphOptions,
): AssetGraphLayout => {
  const g = new dagre.graphlib.Graph({compound: true});
  const config = Object.assign({}, Config[opts.direction], opts.overrides || {});

  g.setGraph(config);
  g.setDefaultEdgeLabel(() => ({}));

  // const shouldRender = (node?: GraphNode) => node && node.definition.opNames.length > 0;
  const shouldRender = (node?: GraphNode) => node;
  const renderedNodes = Object.values(graphData.nodes).filter(shouldRender);
  const expandedGroups = graphData.expandedGroups || [];

  // Identify all the groups
  const groups: {[id: string]: GroupLayout} = {};
  for (const node of renderedNodes) {
    if (node.definition.groupName) {
      const id = groupIdForNode(node);
      groups[id] = groups[id] || {
        id,
        expanded: expandedGroups.includes(id),
        groupName: node.definition.groupName,
        repositoryName: node.definition.repository.name,
        repositoryLocationName: node.definition.repository.location.name,
        bounds: {x: 0, y: 0, width: 0, height: 0},
      };
    }
  }

  // Add all the group boxes to the graph
  const groupsPresent =
    config.groupRendering === 'if-varied' ? Object.keys(groups).length > 1 : true;

  if (groupsPresent) {
    Object.keys(groups).forEach((groupId) => {
      if (expandedGroups.includes(groupId)) {
        // sized based on it's children, but "border" tells Dagre we want cluster-level
        // spacing between the node and others. Necessary because our groups have title bars.
        g.setNode(groupId, {borderType: 'borderRight'});
      } else {
        g.setNode(groupId, {width: ASSET_NODE_WIDTH, height: 110});
      }
    });
  }

  // Add all the nodes inside expanded groups to the graph
  renderedNodes.forEach((node) => {
    if (!groupsPresent || expandedGroups.includes(groupIdForNode(node))) {
      const label =
        config.nodeHeight === 'auto'
          ? getAssetNodeDimensions(node.definition)
          : {width: ASSET_NODE_WIDTH, height: config.nodeHeight};

      g.setNode(node.id, label);
      if (groupsPresent && node.definition.groupName) {
        g.setParent(node.id, groupIdForNode(node));
      }
    }
  });

  const linksToAssetsOutsideGraphedSet: {[id: string]: true} = {};
  const groupIdForAssetId = Object.fromEntries(
    Object.entries(graphData.nodes).map(([id, node]) => [id, groupIdForNode(node)]),
  );

  // Add the edges to the graph, and accumulate a set of "foreign nodes" (for which
  // we have an inbound/outbound edge, but we don't have the `node` in the graphData).
  Object.entries(graphData.downstream).forEach(([upstreamId, graphDataDownstream]) => {
    const downstreamIds = Object.keys(graphDataDownstream);
    downstreamIds.forEach((downstreamId) => {
      if (
        !shouldRender(graphData.nodes[downstreamId]) &&
        !shouldRender(graphData.nodes[upstreamId])
      ) {
        return;
      }
      let v = upstreamId;
      let w = downstreamId;

      const wGroup = groupIdForAssetId[downstreamId];
      if (groupsPresent && wGroup && !expandedGroups.includes(wGroup)) {
        w = wGroup;
      }
      const vGroup = groupIdForAssetId[upstreamId];
      if (groupsPresent && vGroup && !expandedGroups.includes(vGroup)) {
        v = vGroup;
      }
      if (v === w) {
        return;
      }

      g.setEdge({v, w}, {weight: 1});

      if (!shouldRender(graphData.nodes[downstreamId])) {
        linksToAssetsOutsideGraphedSet[downstreamId] = true;
      } else if (!shouldRender(graphData.nodes[upstreamId])) {
        linksToAssetsOutsideGraphedSet[upstreamId] = true;
      }
    });
  });

  // Add all the link nodes to the graph
  Object.keys(linksToAssetsOutsideGraphedSet).forEach((id) => {
    const path = JSON.parse(id);
    const label = path[path.length - 1] || '';
    g.setNode(id, getAssetLinkDimensions(label, opts));
  });

  dagre.layout(g);

  let maxWidth = 1;
  let maxHeight = 1;

  const nodes: {[id: string]: AssetLayout} = {};

  g.nodes().forEach((id) => {
    const dagreNode = g.node(id);
    if (!dagreNode?.x || !dagreNode?.width) {
      return;
    }
    const bounds = {
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
      width: dagreNode.width,
      height: dagreNode.height,
    };
    if (!isGroupId(id)) {
      nodes[id] = {id, bounds};
    } else if (!expandedGroups.includes(id)) {
      const group = groups[id]!;
      group.bounds = bounds;
    }

    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  // Apply bounds to the groups based on the nodes inside them
  if (groupsPresent) {
    for (const node of renderedNodes) {
      const nodeLayout = nodes[node.id];
      if (nodeLayout && node.definition.groupName) {
        const groupId = groupIdForNode(node);
        const group = groups[groupId]!;
        group.bounds =
          group.bounds.width === 0
            ? nodeLayout.bounds
            : extendBounds(group.bounds, nodeLayout.bounds);
      }
    }
    for (const group of Object.values(groups)) {
      if (group.expanded) {
        group.bounds = padBounds(group.bounds, {
          x: 15,
          top: config.groupPaddingTop,
          bottom: config.groupPaddingBottom,
        });
      }
    }
  }

  const edges: AssetLayoutEdge[] = [];

  g.edges().forEach((e) => {
    const v = g.node(e.v);
    const w = g.node(e.w);
    if (!v || !w) {
      return;
    }
    const vXInset = !!linksToAssetsOutsideGraphedSet[e.v] ? 16 : 24;
    const wXInset = !!linksToAssetsOutsideGraphedSet[e.w] ? 16 : 24;

    // Ignore the coordinates from dagre and use the top left + bottom left of the
    edges.push(
      opts.direction === 'horizontal'
        ? {
            from: {x: v.x + v.width / 2, y: v.y},
            fromId: e.v,
            to: {x: w.x - w.width / 2 - 5, y: w.y},
            toId: e.w,
          }
        : {
            from: {x: v.x - v.width / 2 + vXInset, y: v.y - 30 + v.height / 2},
            fromId: e.v,
            to: {x: w.x - w.width / 2 + wXInset, y: w.y + 20 - w.height / 2},
            toId: e.w,
          },
    );
  });

  return {
    nodes,
    edges,
    width: maxWidth + MARGIN,
    height: maxHeight + MARGIN,
    groups: groupsPresent ? groups : {},
  };
};

export const ASSET_LINK_NAME_MAX_LENGTH = 30;

export const getAssetLinkDimensions = (label: string, opts: LayoutAssetGraphOptions) => {
  return opts.direction === 'horizontal'
    ? {width: 32 + 7.1 * Math.min(ASSET_LINK_NAME_MAX_LENGTH, label.length), height: 50}
    : {width: 106, height: 50};
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

export const ASSET_NODE_WIDTH = 320;
export const ASSET_NODE_NAME_MAX_LENGTH = 38;

export const getAssetNodeDimensions = (def: {
  assetKey: {path: string[]};
  opNames: string[];
  isSource: boolean;
  isObservable: boolean;
  isPartitioned: boolean;
  graphName: string | null;
  description?: string | null;
  computeKind: string | null;
  changedReasons?: ChangeReason[];
}) => {
  const width = ASSET_NODE_WIDTH;

  let height = 100; // top tags area + name + description

  if (def.isSource && def.isObservable) {
    height += 30; // status row
  } else {
    height += 26; // status row
    if (def.isPartitioned) {
      height += 40;
    }
  }
  if (def.changedReasons?.length) {
    height += 30;
  }

  height += 30; // tags beneath

  return {width, height};
};
