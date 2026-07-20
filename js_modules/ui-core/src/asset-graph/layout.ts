import * as dagre from 'dagre';

import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {
  GraphData,
  GraphId,
  ancestorGroupIds,
  groupIdForNode,
  isGroupId,
  parseGroupId,
} from './Utils';
import {applyAssetGroupLineageRouting} from './assetGroupLineageRouting';
import type {IBounds, IPoint} from '../graph/common';

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
  // Depth in the group hierarchy (0 = top-level).
  depth: number;
}
export type AssetLayoutEdge = {
  from: IPoint;
  fromId: string;
  to: IPoint;
  toId: string;
  sourceBoundary?: number;
  targetBoundary?: number;
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
  ranker?: 'tight-tree' | 'longest-path' | 'network-simplex';
};

export type LayoutAssetGraphOptions = {
  direction: AssetLayoutDirection;
  flagAssetGraphGroupsPerCodeLocation: boolean;
  overrides?: Partial<LayoutAssetGraphConfig>;
  facets: AssetNodeFacet[];
  forceLargeGraph?: boolean;
};

export const Config = {
  horizontal: {
    ranker: 'tight-tree',
    marginx: MARGIN,
    marginy: MARGIN,
    ranksep: 60,
    rankdir: 'LR',
    edgesep: 90,
    nodesep: -10,
    nodeHeight: 'auto' as 'auto' | number,
    groupPaddingTop: 65,
    groupPaddingBottom: 16,
    groupRendering: 'if-varied' as 'if-varied' | 'always',
    clusterpaddingtop: 100,
  },
  vertical: {
    ranker: 'tight-tree',
    marginx: MARGIN,
    marginy: MARGIN,
    ranksep: 20,
    rankdir: 'TB',
    nodesep: 40,
    edgesep: 10,
    nodeHeight: 'auto' as 'auto' | number,
    groupPaddingTop: 55,
    groupPaddingBottom: 16,
    groupRendering: 'if-varied' as 'if-varied' | 'always',
  },
};

export const layoutAssetGraph = (
  graphData: GraphData,
  opts: LayoutAssetGraphOptions,
): AssetGraphLayout => {
  try {
    return layoutAssetGraphImpl(graphData, opts);
  } catch {
    try {
      return layoutAssetGraphImpl(graphData, {
        ...opts,
        overrides: {
          ranker: 'longest-path',
        },
      });
    } catch {
      return layoutAssetGraphImpl(graphData, {...opts, overrides: {ranker: 'network-simplex'}});
    }
  }
};

export const layoutAssetGraphImpl = (
  graphData: GraphData,
  opts: LayoutAssetGraphOptions,
): AssetGraphLayout => {
  const facets = new Set<AssetNodeFacet>(opts.facets);
  const g = new dagre.graphlib.Graph({compound: true});
  const config = Object.assign({}, Config[opts.direction], opts.overrides || {});

  g.setGraph(config);
  g.setDefaultEdgeLabel(() => ({}));

  const renderedNodes = Object.values(graphData.nodes);
  // Expanding a child implicitly expands all of its ancestors — otherwise the
  // child would be hidden under a collapsed parent.
  const expandedGroupsSet = new Set<string>();
  for (const id of graphData.expandedGroups || []) {
    expandedGroupsSet.add(id);
    for (const anc of ancestorGroupIds(id)) {
      expandedGroupsSet.add(anc);
    }
  }

  const groups: {[id: string]: GroupLayout} = {};
  const sampleNodeForGroupId = new Map<string, (typeof renderedNodes)[number]>();
  // Track which (repo, location) pairs contribute to each group id. When a
  // synthetic ancestor spans multiple code locations (e.g. flag off, two
  // repos both define `marketing/foo`), we can't attribute it to one of
  // them — clear the repo fields so callers like onFilterToGroup skip the
  // `code_location:` filter that would otherwise hide the other location.
  const locationsForGroupId = new Map<string, Set<string>>();
  const recordLocation = (groupId: string, node: (typeof renderedNodes)[number]) => {
    const key = `${node.definition.repository.name}|${node.definition.repository.location.name}`;
    let set = locationsForGroupId.get(groupId);
    if (!set) {
      set = new Set();
      locationsForGroupId.set(groupId, set);
    }
    set.add(key);
  };

  for (const node of renderedNodes) {
    if (!node.definition.groupName) {
      continue;
    }
    const leafId = groupIdForNode(node);
    if (!sampleNodeForGroupId.has(leafId)) {
      sampleNodeForGroupId.set(leafId, node);
    }
    recordLocation(leafId, node);
    for (const ancId of ancestorGroupIds(leafId)) {
      if (!sampleNodeForGroupId.has(ancId)) {
        sampleNodeForGroupId.set(ancId, node);
      }
      recordLocation(ancId, node);
    }
  }

  for (const [id, sample] of sampleNodeForGroupId.entries()) {
    const parsed = parseGroupId(id);
    const depth = parsed ? Math.max(parsed.segments.length - 1, 0) : 0;
    const isMultiLocation = (locationsForGroupId.get(id)?.size ?? 0) > 1;
    groups[id] = {
      id,
      expanded: expandedGroupsSet.has(id),
      groupName: parsed ? parsed.segments.join('/') : id,
      repositoryName: isMultiLocation ? '' : sample.definition.repository.name,
      repositoryLocationName: isMultiLocation ? '' : sample.definition.repository.location.name,
      bounds: {x: 0, y: 0, width: 0, height: 0},
      depth,
    };
  }

  // A collapsed ancestor hides its entire subtree.
  const allGroupIds = new Set(Object.keys(groups));
  const visibleGroupIds = new Set<string>();
  for (const id of allGroupIds) {
    const ancs = ancestorGroupIds(id);
    if (ancs.every((anc) => !allGroupIds.has(anc) || expandedGroupsSet.has(anc))) {
      visibleGroupIds.add(id);
    }
  }

  const deepestVisibleAncestor = (id: string): string | undefined => {
    const ancs = ancestorGroupIds(id);
    for (let i = ancs.length - 1; i >= 0; i--) {
      const anc = ancs[i];
      if (anc !== undefined && visibleGroupIds.has(anc)) {
        return anc;
      }
    }
    return undefined;
  };

  const groupsPresent = config.groupRendering === 'if-varied' ? allGroupIds.size > 1 : true;

  if (groupsPresent) {
    for (const id of visibleGroupIds) {
      if (expandedGroupsSet.has(id)) {
        // borderType lets us reference the cluster as an edge endpoint.
        g.setNode(id, {borderType: 'borderRight'});
      } else {
        g.setNode(id, {width: ASSET_NODE_WIDTH, height: 110});
      }
      const parent = deepestVisibleAncestor(id);
      if (parent !== undefined) {
        g.setParent(id, parent);
      }
    }
  }

  renderedNodes.forEach((node) => {
    const leafId = node.definition.groupName ? groupIdForNode(node) : null;
    const assetVisible =
      !groupsPresent || !leafId || (visibleGroupIds.has(leafId) && expandedGroupsSet.has(leafId));
    if (!assetVisible) {
      return;
    }

    const label =
      config.nodeHeight === 'auto'
        ? getAssetNodeDimensions(facets)
        : {width: ASSET_NODE_WIDTH, height: config.nodeHeight};

    g.setNode(node.id, label);
    if (groupsPresent && leafId) {
      g.setParent(node.id, leafId);
    }
  });

  const linksToAssetsOutsideGraphedSet: {[id: string]: true} = {};

  const edgeEndpointById: {[id: string]: string} = {};
  if (groupsPresent) {
    for (const [id, node] of Object.entries(graphData.nodes)) {
      if (!node.definition.groupName) {
        continue;
      }
      const leafId = groupIdForNode(node);
      if (visibleGroupIds.has(leafId) && expandedGroupsSet.has(leafId)) {
        edgeEndpointById[id] = id;
      } else if (visibleGroupIds.has(leafId)) {
        edgeEndpointById[id] = leafId;
      } else {
        const anc = deepestVisibleAncestor(leafId);
        edgeEndpointById[id] = anc ?? id;
      }
    }
  }

  const edgeEndpointFor = (assetId: string): string => edgeEndpointById[assetId] ?? assetId;

  Object.entries(graphData.downstream).forEach(([upstreamId, graphDataDownstream]) => {
    const downstreamIds = Object.keys(graphDataDownstream);
    downstreamIds.forEach((downstreamId) => {
      if (!graphData.nodes[downstreamId] && !graphData.nodes[upstreamId]) {
        return;
      }
      const v = edgeEndpointFor(upstreamId);
      const w = edgeEndpointFor(downstreamId);
      if (v === w) {
        return;
      }

      g.setEdge({v, w}, {weight: 1});

      if (!graphData.nodes[downstreamId]) {
        linksToAssetsOutsideGraphedSet[downstreamId] = true;
      } else if (!graphData.nodes[upstreamId]) {
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
    } else if (!expandedGroupsSet.has(id)) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const group = groups[id]!;
      group.bounds = bounds;
    }

    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  // Walk groups deepest-first so each group's header padding is baked in
  // before its bounds get propagated to its visible ancestor.
  if (groupsPresent) {
    const accumulate = (groupId: string, childBounds: IBounds) => {
      const group = groups[groupId];
      if (!group) {
        return;
      }
      group.bounds =
        group.bounds.width === 0 ? childBounds : extendBounds(group.bounds, childBounds);
    };

    for (const node of renderedNodes) {
      const leafId = node.definition.groupName ? groupIdForNode(node) : null;
      if (!leafId) {
        continue;
      }
      const nodeLayout = nodes[node.id];
      if (!nodeLayout) {
        continue;
      }
      accumulate(leafId, nodeLayout.bounds);
    }

    const groupsByDepthDesc = Object.values(groups).sort((a, b) => b.depth - a.depth);
    for (const group of groupsByDepthDesc) {
      if (!visibleGroupIds.has(group.id) || group.bounds.width === 0) {
        continue;
      }
      if (group.expanded) {
        group.bounds = padBounds(group.bounds, {
          x: 15,
          top: config.groupPaddingTop,
          bottom: config.groupPaddingBottom,
        });
      }
      const anc = deepestVisibleAncestor(group.id);
      if (anc !== undefined) {
        accumulate(anc, group.bounds);
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

  // Hidden ancestors (under a collapsed parent) would otherwise render as
  // zero-width artifacts.
  const visibleGroups: {[id: string]: GroupLayout} = {};
  for (const id of visibleGroupIds) {
    const group = groups[id];
    if (group && group.bounds.width > 0) {
      visibleGroups[id] = group;
    }
  }

  const finalGroups = groupsPresent ? visibleGroups : {};
  const finalVisibleGroupIds = new Set(Object.keys(finalGroups));
  const groupParentById: Record<string, string | null> = {};
  for (const id of finalVisibleGroupIds) {
    const ancestors = ancestorGroupIds(id);
    const immediateParent = ancestors[ancestors.length - 1];
    groupParentById[id] =
      immediateParent !== undefined && finalVisibleGroupIds.has(immediateParent)
        ? immediateParent
        : null;
  }

  const ownerGroupByNodeId: Record<string, string | null> = {};
  for (const node of renderedNodes) {
    if (!nodes[node.id]) {
      continue;
    }
    const leafId = node.definition.groupName ? groupIdForNode(node) : null;
    ownerGroupByNodeId[node.id] = leafId && finalVisibleGroupIds.has(leafId) ? leafId : null;
  }

  const endpointGroupById: Record<string, string | null> = {};
  for (const edge of edges) {
    for (const endpointId of [edge.fromId, edge.toId]) {
      endpointGroupById[endpointId] = isGroupId(endpointId)
        ? endpointId
        : (ownerGroupByNodeId[endpointId] ?? null);
    }
  }

  const baseline: AssetGraphLayout = {
    nodes,
    edges,
    width: maxWidth + MARGIN,
    height: maxHeight + MARGIN,
    groups: finalGroups,
  };

  return applyAssetGroupLineageRouting(baseline, {
    direction: opts.direction,
    ranksep: Number(config.ranksep ?? Config[opts.direction].ranksep),
    trailingGroupPadding: opts.direction === 'horizontal' ? 15 : Number(config.groupPaddingBottom),
    margin: MARGIN,
    groupParentById,
    ownerGroupByNodeId,
    endpointGroupById,
  });
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
export const ASSET_NODE_TAGS_HEIGHT = 28;
export const ASSET_NODE_STATUS_ROW_HEIGHT = 25;

export const ASSET_NODE_NAME_MAX_LENGTH = 31;

export const getAssetNodeDimensions = (facets: Set<AssetNodeFacet>) => {
  let height = 0;

  if (facets.size === 0) {
    height = 60;
  } else {
    height = 50; // box padding + border + name
    height += ASSET_NODE_STATUS_ROW_HEIGHT * facets.size;
  }

  return {width: ASSET_NODE_WIDTH, height};
};
