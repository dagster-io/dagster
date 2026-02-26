import {GraphNode, groupIdForNode} from './Utils';
import {invariant} from '../util/invariant';

export type PreflightCheckResult =
  | {hasCycles: true; nodeCount: null; edgeCount: null; longestPath: null}
  | {hasCycles: false; nodeCount: number; edgeCount: number; longestPath: number};

/**
 * Analyzes a directed graph to detect cycles and compute the longest path.
 * Uses Kahn's algorithm for topological sort (which detects cycles) followed
 * by traversal of the topological order to compute longest path.
 * Time complexity: O(V + E), Space complexity: O(V)
 *
 * When expandedGroups is provided (for asset graphs), nodes in collapsed groups
 * are counted as a single node per group, giving an accurate count of what will
 * actually be rendered. This prevents "graph too large" errors when most nodes
 * are in collapsed groups.
 */
export const runPreflightChecks = (
  graphData: {
    nodes: {[id: string]: GraphNode | unknown};
    downstream: {[id: string]: {[childId: string]: boolean}};
  },
  expandedGroups?: string[],
): PreflightCheckResult => {
  // First, check for cycles in the ORIGINAL graph (before any group collapsing).
  // We must do this on the original graph because collapsing groups can create
  // "pseudo-cycles" even in a valid DAG. For example: A->C, C->B where A and B
  // are in the same collapsed group G creates G->C->G in the visible graph.
  const originalNodeIds = Object.keys(graphData.nodes);
  const originalResult = topoSortKahn(originalNodeIds, graphData.downstream);
  if (originalResult.hasCycles) {
    return {hasCycles: true, edgeCount: null, nodeCount: null, longestPath: null};
  }

  // Early exit: if no group collapsing requested, use original graph directly
  if (!expandedGroups) {
    return {
      hasCycles: false,
      nodeCount: originalNodeIds.length,
      edgeCount: countEdges(graphData.downstream),
      longestPath: computeLongestPath(
        originalNodeIds,
        originalResult.topoOrder,
        graphData.downstream,
      ),
    };
  }

  // Now compute node/edge counts and longest path on the VISIBLE graph
  // (with groups collapsed) since this reflects what will actually be rendered.
  const {visibleIdCache} = buildVisibleIDMapping(graphData, expandedGroups);
  const visibleNodeIds = new Set(visibleIdCache.values());
  const nodeIds = Array.from(visibleNodeIds);
  const nodeCount = nodeIds.length;

  // Fast lookup for edge remapping
  const getVisibleId = (nodeId: string): string => visibleIdCache.get(nodeId) ?? nodeId;

  if (nodeCount === 0) {
    return {hasCycles: false, edgeCount: 0, nodeCount: 0, longestPath: 0};
  }

  // Build remapped downstream edges (edges between visible nodes, skipping internal edges)
  const visibleDownstream: {[id: string]: {[childId: string]: boolean}} = {};
  for (const upstreamId of Object.keys(graphData.downstream)) {
    const downstreamEdges = graphData.downstream[upstreamId];
    if (!downstreamEdges) {
      continue;
    }
    const visibleUpstream = getVisibleId(upstreamId);
    for (const downstreamId of Object.keys(downstreamEdges)) {
      const visibleDownstreamId = getVisibleId(downstreamId);
      if (visibleUpstream === visibleDownstreamId) {
        continue; // Skip self-edges (internal edges within a collapsed group)
      }
      const edges = visibleDownstream[visibleUpstream] || {};
      edges[visibleDownstreamId] = true;
      visibleDownstream[visibleUpstream] = edges;
    }
  }

  // Compute longest path on the visible graph using topological order.
  // The visible graph may have "pseudo-cycles" from group collapsing, but we've
  // already verified the original graph is a DAG. If pseudo-cycles exist, fall
  // back to the original graph's longest path (an upper bound, since collapsing
  // can only shorten paths).
  const visibleResult = topoSortKahn(nodeIds, visibleDownstream);
  const longestPath = visibleResult.hasCycles
    ? computeLongestPath(originalNodeIds, originalResult.topoOrder, graphData.downstream)
    : computeLongestPath(nodeIds, visibleResult.topoOrder, visibleDownstream);

  return {hasCycles: false, nodeCount, edgeCount: countEdges(visibleDownstream), longestPath};
};

/** Counts total edges in a downstream adjacency map. */
function countEdges(downstream: {[id: string]: {[childId: string]: boolean}}): number {
  let count = 0;
  for (const upstreamId of Object.keys(downstream)) {
    const edges = downstream[upstreamId];
    if (edges) {
      count += Object.keys(edges).length;
    }
  }
  return count;
}

/**
 * Runs Kahn's algorithm for topological sort.
 * Returns hasCycles=true if the graph contains cycles.
 * Returns the topological order if the graph is a DAG.
 */
function topoSortKahn(
  nodeIds: string[],
  downstream: {[id: string]: {[childId: string]: boolean}},
): {hasCycles: true; topoOrder: null} | {hasCycles: false; topoOrder: string[]} {
  const nodeCount = nodeIds.length;
  if (nodeCount === 0) {
    return {hasCycles: false, topoOrder: []};
  }

  // Compute in-degrees
  const inDegree = new Map<string, number>();
  for (const node of nodeIds) {
    inDegree.set(node, 0);
  }
  for (const node of nodeIds) {
    const edges = downstream[node];
    if (edges) {
      for (const neighbor in edges) {
        if (inDegree.has(neighbor)) {
          const degree = inDegree.get(neighbor);
          invariant(degree !== undefined, 'Degree exists');
          inDegree.set(neighbor, degree + 1);
        }
      }
    }
  }

  // Kahn's algorithm - process nodes with in-degree 0
  const queue: string[] = [];
  for (const [node, degree] of inDegree) {
    if (degree === 0) {
      queue.push(node);
    }
  }

  const topoOrder: string[] = [];
  let head = 0;
  while (head < queue.length) {
    const node = queue[head++];
    invariant(node !== undefined, 'Node exists');
    topoOrder.push(node);

    const edges = downstream[node];
    if (edges) {
      for (const neighbor in edges) {
        if (inDegree.has(neighbor)) {
          const degree = inDegree.get(neighbor);
          invariant(degree !== undefined, 'Degree exists');
          const newDegree = degree - 1;
          inDegree.set(neighbor, newDegree);
          if (newDegree === 0) {
            queue.push(neighbor);
          }
        }
      }
    }
  }

  // Cycle detection: if we didn't process all nodes, there's a cycle
  if (topoOrder.length !== nodeCount) {
    return {hasCycles: true, topoOrder: null};
  }

  return {hasCycles: false, topoOrder};
}

/**
 * Computes the longest path in a DAG using dynamic programming on topological order.
 * Assumes the graph has no cycles (caller should check first).
 */
function computeLongestPath(
  nodeIds: string[],
  topoOrder: string[],
  downstream: {[id: string]: {[childId: string]: boolean}},
): number {
  if (nodeIds.length === 0) {
    return 0;
  }

  const dist = new Map<string, number>();
  for (const node of nodeIds) {
    dist.set(node, 0);
  }

  let longestPath = 0;
  for (const node of topoOrder) {
    const edges = downstream[node];
    if (edges) {
      for (const neighbor in edges) {
        if (dist.has(neighbor)) {
          const nodeDist = dist.get(node);
          const neighborDist = dist.get(neighbor);
          invariant(nodeDist !== undefined, 'Node dist exists');
          invariant(neighborDist !== undefined, 'Neighbor dist exists');
          const newDist = nodeDist + 1;
          if (newDist > neighborDist) {
            dist.set(neighbor, newDist);
            if (newDist > longestPath) {
              longestPath = newDist;
            }
          }
        }
      }
    }
  }

  return longestPath;
}

function buildVisibleIDMapping(
  graphData: {
    nodes: {[id: string]: GraphNode | unknown};
    downstream: {[id: string]: {[childId: string]: boolean}};
  },
  expandedGroups?: string[],
) {
  // Build a mapping from raw node IDs to "visible" IDs. When expandedGroups is provided,
  // nodes in collapsed groups map to their group ID (so they're counted as one node).
  // When not provided (op graphs), each node maps to itself.
  //
  // Note: Like layoutAssetGraph, we only apply group collapsing when there are multiple
  // groups present. If there's only one group, all nodes are rendered individually
  // regardless of expandedGroups.
  const expandedGroupsSet = expandedGroups ? new Set(expandedGroups) : null;

  // Single pass: build visible ID cache and count unique groups simultaneously
  // This avoids iterating over all nodes twice and caches groupIdForNode results
  const visibleIdCache = new Map<string, string>();
  const uniqueGroups = new Set<string>();

  for (const nodeId of Object.keys(graphData.nodes)) {
    if (!expandedGroupsSet) {
      visibleIdCache.set(nodeId, nodeId);
      continue;
    }
    const node = graphData.nodes[nodeId] as GraphNode | undefined;
    if (!node || !('definition' in node)) {
      visibleIdCache.set(nodeId, nodeId);
      continue;
    }
    const groupId = groupIdForNode(node);
    if (node.definition.groupName) {
      uniqueGroups.add(groupId);
    }

    const visibleId = expandedGroupsSet.has(groupId) ? nodeId : groupId;
    visibleIdCache.set(nodeId, visibleId);
  }

  // Groups only matter when there's more than one (matches 'if-varied' behavior in layout).
  // If only a single group is present, switch visibleIdCache back to node IDs
  const groupsPresent = uniqueGroups.size > 1;
  if (expandedGroupsSet && !groupsPresent) {
    for (const nodeId of visibleIdCache.keys()) {
      visibleIdCache.set(nodeId, nodeId);
    }
  }

  return {expandedGroupsSet, visibleIdCache};
}
