import {
  AssetGraphLayout,
  AssetLayoutDirection,
  AssetLayoutEdge,
  Config,
  GroupLayout,
  computeEdgeEndpoints,
  extendBounds,
  padBounds,
} from './layout';
import {IPoint} from '../graph/common';

/**
 * Applies manual position overrides to a Dagre-computed AssetGraphLayout.
 * Returns a new layout with overridden node positions, recomputed edges,
 * and recomputed group/canvas bounds. The original layout is not mutated.
 *
 * `overrides` maps nodeId → {x, y} top-left position.
 * `nodeToGroupId` maps nodeId → groupId for explicit group membership.
 */
export function applyPositionOverrides(
  layout: AssetGraphLayout,
  overrides: Record<string, IPoint>,
  direction: AssetLayoutDirection,
  nodeToGroupId?: Record<string, string>,
): AssetGraphLayout {
  if (Object.keys(overrides).length === 0) {
    return layout;
  }

  // Clone nodes with overrides applied
  const nodes: AssetGraphLayout['nodes'] = {};
  for (const [id, node] of Object.entries(layout.nodes)) {
    const override = overrides[id];
    nodes[id] = override
      ? {id: node.id, bounds: {...node.bounds, x: override.x, y: override.y}}
      : node;
  }

  // Build a lookup: nodeId → bounds (for edge recomputation)
  const boundsById: Record<string, {x: number; y: number; width: number; height: number}> = {};
  for (const [id, node] of Object.entries(nodes)) {
    boundsById[id] = node.bounds;
  }
  // Include group bounds (with overrides applied for collapsed groups)
  for (const [id, group] of Object.entries(layout.groups)) {
    if (!boundsById[id]) {
      const override = overrides[id];
      boundsById[id] = override ? {...group.bounds, x: override.x, y: override.y} : group.bounds;
    }
  }

  // Recompute edges based on updated positions
  const linkNodeSet = new Set(layout.linkNodeIds);
  const edges: AssetLayoutEdge[] = layout.edges.map((edge) => {
    const fromBounds = boundsById[edge.fromId];
    const toBounds = boundsById[edge.toId];
    if (!fromBounds || !toBounds) {
      return edge;
    }
    const fromXInset = linkNodeSet.has(edge.fromId) ? 16 : 24;
    const toXInset = linkNodeSet.has(edge.toId) ? 16 : 24;
    const {from, to} = computeEdgeEndpoints(fromBounds, toBounds, direction, fromXInset, toXInset);
    return {from, fromId: edge.fromId, to, toId: edge.toId};
  });

  // Recompute group bounds for expanded groups whose children moved
  const config = direction === 'horizontal' ? Config.horizontal : Config.vertical;
  const groups: {[name: string]: GroupLayout} = {};
  for (const [id, group] of Object.entries(layout.groups)) {
    if (!group.expanded) {
      const override = overrides[id];
      groups[id] = override
        ? {...group, bounds: {...group.bounds, x: override.x, y: override.y}}
        : group;
      continue;
    }
    // Recompute bounds from child nodes using explicit group membership
    let groupBounds = {x: 0, y: 0, width: 0, height: 0};
    let first = true;
    for (const [nodeId, node] of Object.entries(nodes)) {
      const belongsToGroup = nodeToGroupId ? nodeToGroupId[nodeId] === id : false;
      if (belongsToGroup) {
        groupBounds = first ? node.bounds : extendBounds(groupBounds, node.bounds);
        first = false;
      }
    }
    if (!first) {
      groups[id] = {
        ...group,
        bounds: padBounds(groupBounds, {
          x: 15,
          top: config.groupPaddingTop,
          bottom: config.groupPaddingBottom,
        }),
      };
    } else {
      groups[id] = group;
    }
  }

  // Recompute canvas extents
  let maxX = 1;
  let maxY = 1;
  for (const node of Object.values(nodes)) {
    maxX = Math.max(maxX, node.bounds.x + node.bounds.width);
    maxY = Math.max(maxY, node.bounds.y + node.bounds.height);
  }
  for (const group of Object.values(groups)) {
    maxX = Math.max(maxX, group.bounds.x + group.bounds.width);
    maxY = Math.max(maxY, group.bounds.y + group.bounds.height);
  }

  return {
    nodes,
    edges,
    groups,
    linkNodeIds: layout.linkNodeIds,
    // Use the original layout dimensions as a minimum so the canvas never shrinks when
    // nodes are dragged toward the origin, preventing jarring viewport repositioning.
    width: Math.max(layout.width, maxX + 100),
    height: Math.max(layout.height, maxY + 100),
  };
}
