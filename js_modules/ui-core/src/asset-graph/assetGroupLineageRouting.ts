import type {IBounds} from '../graph/common';

export type GroupParentById = Record<string, string | null>;

export type RoutingDirection = 'horizontal' | 'vertical';

export type RoutingGroup = {bounds: IBounds; expanded: boolean};

export type BranchConstraint = {
  sourceBranchId: string;
  targetBranchId: string;
  sourceUsesGroupEnd: boolean;
  sourceBaseExit: number;
  targetBaseEntry: number;
};

export type EdgeRouteInfo = BranchConstraint;

export type RoutingLayoutEdge = {
  from: {x: number; y: number};
  fromId: string;
  to: {x: number; y: number};
  toId: string;
  sourceBoundary?: number;
  targetBoundary?: number;
};

export type RoutingLayout = {
  width: number;
  height: number;
  nodes: Record<string, {id: string; bounds: IBounds}>;
  groups: Record<string, {id: string; bounds: IBounds; expanded: boolean}>;
  edges: RoutingLayoutEdge[];
};

export type ApplyAssetGroupRoutingOptions = {
  direction: RoutingDirection;
  ranksep: number;
  trailingGroupPadding: number;
  margin: number;
  groupParentById: GroupParentById;
  ownerGroupByNodeId: Record<string, string | null>;
  endpointGroupById: Record<string, string | null>;
};

export type AssetGroupConstraintInput = {
  direction: RoutingDirection;
  ranksep: number;
  trailingGroupPadding: number;
  groups: Record<string, RoutingGroup>;
  parentById: GroupParentById;
  constraints: BranchConstraint[];
};

export type AssetGroupConstraintSolution = {
  shiftByGroupId: Record<string, number>;
  endByGroupId: Record<string, number>;
  componentByGroupId: Record<string, string>;
};

const primaryStart = (bounds: IBounds, direction: RoutingDirection) =>
  direction === 'horizontal' ? bounds.x : bounds.y;

const primaryEnd = (bounds: IBounds, direction: RoutingDirection) =>
  primaryStart(bounds, direction) + (direction === 'horizontal' ? bounds.width : bounds.height);

export type GroupAncestryIndex = {
  lowestCommonAncestor: (a: string, b: string) => string | null;
  branchBelow: (groupId: string, ancestorId: string | null) => string | null;
};

export const buildGroupAncestryIndex = (parentById: GroupParentById): GroupAncestryIndex => {
  const ids = Object.keys(parentById).sort();
  const indexById = new Map<string, number>();
  for (let index = 0; index < ids.length; index++) {
    indexById.set(ids[index]!, index);
  }
  const groupCount = ids.length;

  const parent = new Int32Array(groupCount);
  parent.fill(-1);
  let hasNestedGroups = false;
  for (let index = 0; index < groupCount; index++) {
    const parentId = parentById[ids[index]!];
    if (parentId === null) {
      continue;
    }
    if (parentId === undefined) {
      throw new Error('Missing visible asset group parent: undefined');
    }
    const parentIndex = indexById.get(parentId);
    if (parentIndex === undefined) {
      throw new Error(`Missing visible asset group parent: ${parentId}`);
    }
    parent[index] = parentIndex;
    hasNestedGroups = true;
  }

  const requireIndex = (id: string) => {
    const index = indexById.get(id);
    if (index === undefined) {
      throw new Error(`Unknown visible asset group: ${id}`);
    }
    return index;
  };

  if (!hasNestedGroups) {
    return {
      lowestCommonAncestor: (a, b) => {
        requireIndex(a);
        requireIndex(b);
        return a === b ? a : null;
      },
      branchBelow: (groupId, ancestorId) => {
        requireIndex(groupId);
        if (ancestorId !== null) {
          requireIndex(ancestorId);
        }
        return ancestorId === null ? groupId : null;
      },
    };
  }

  const depth = new Int32Array(groupCount);
  const root = new Int32Array(groupCount);
  const visiting = new Uint8Array(groupCount);
  depth.fill(-1);
  root.fill(-1);

  for (let start = 0; start < groupCount; start++) {
    if (visiting[start] === 2) {
      continue;
    }

    const path: number[] = [];
    let current = start;
    while (current !== -1 && visiting[current] === 0) {
      visiting[current] = 1;
      path.push(current);
      current = parent[current]!;
    }

    if (current !== -1 && visiting[current] === 1) {
      throw new Error('Asset group parent cycle');
    }

    for (let pathIndex = path.length - 1; pathIndex >= 0; pathIndex--) {
      const groupIndex = path[pathIndex]!;
      const parentIndex = parent[groupIndex]!;
      if (parentIndex === -1) {
        depth[groupIndex] = 0;
        root[groupIndex] = groupIndex;
      } else {
        depth[groupIndex] = depth[parentIndex]! + 1;
        root[groupIndex] = root[parentIndex]!;
      }
      visiting[groupIndex] = 2;
    }
  }

  const levelCount = Math.ceil(Math.log2(Math.max(1, groupCount))) + 1;
  const ancestors: Int32Array[] = [parent];
  for (let level = 1; level < levelCount; level++) {
    const previous = ancestors[level - 1]!;
    const current = new Int32Array(groupCount);
    current.fill(-1);
    for (let index = 0; index < groupCount; index++) {
      const previousAncestor = previous[index]!;
      if (previousAncestor !== -1) {
        current[index] = previous[previousAncestor]!;
      }
    }
    ancestors.push(current);
  }

  const lift = (index: number, distance: number) => {
    let current = index;
    let remaining = distance;
    let level = 0;
    while (remaining > 0 && current !== -1) {
      if (remaining % 2 === 1) {
        current = ancestors[level]![current]!;
      }
      remaining = Math.floor(remaining / 2);
      level++;
    }
    return current;
  };

  const lowestCommonAncestorIndex = (a: number, b: number) => {
    if (root[a] !== root[b]) {
      return -1;
    }

    let left = a;
    let right = b;
    if (depth[left]! < depth[right]!) {
      right = lift(right, depth[right]! - depth[left]!);
    } else if (depth[left]! > depth[right]!) {
      left = lift(left, depth[left]! - depth[right]!);
    }
    if (left === right) {
      return left;
    }

    for (let level = levelCount - 1; level >= 0; level--) {
      const leftAncestor = ancestors[level]![left]!;
      const rightAncestor = ancestors[level]![right]!;
      if (leftAncestor !== rightAncestor) {
        left = leftAncestor;
        right = rightAncestor;
      }
    }
    return parent[left]!;
  };

  const lowestCommonAncestor = (a: string, b: string) => {
    const ancestorIndex = lowestCommonAncestorIndex(requireIndex(a), requireIndex(b));
    return ancestorIndex === -1 ? null : ids[ancestorIndex]!;
  };

  const branchBelow = (groupId: string, ancestorId: string | null) => {
    const groupIndex = requireIndex(groupId);
    if (ancestorId === null) {
      return ids[root[groupIndex]!]!;
    }

    const ancestorIndex = requireIndex(ancestorId);
    if (groupIndex === ancestorIndex) {
      return null;
    }
    if (lowestCommonAncestorIndex(groupIndex, ancestorIndex) !== ancestorIndex) {
      return null;
    }

    const branchIndex = lift(groupIndex, depth[groupIndex]! - depth[ancestorIndex]! - 1);
    return ids[branchIndex]!;
  };

  return {lowestCommonAncestor, branchBelow};
};

const buildConstraintComponents = (
  ids: string[],
  indexById: Map<string, number>,
  constraints: BranchConstraint[],
  columns?: ConstraintColumns,
) => {
  const groupCount = ids.length;
  const edgeCount = columns?.count ?? constraints.length;
  const sourceByEdge = new Int32Array(edgeCount);
  const targetByEdge = new Int32Array(edgeCount);
  const outgoingCount = new Int32Array(groupCount);
  const incomingCount = new Int32Array(groupCount);
  for (let edgeIndex = 0; edgeIndex < edgeCount; edgeIndex++) {
    const sourceBranchId = columns
      ? columns.sourceBranchIds[edgeIndex]!
      : constraints[edgeIndex]!.sourceBranchId;
    const targetBranchId = columns
      ? columns.targetBranchIds[edgeIndex]!
      : constraints[edgeIndex]!.targetBranchId;
    const source = indexById.get(sourceBranchId);
    const target = indexById.get(targetBranchId);
    if (source === undefined) {
      throw new Error(`Unknown asset group constraint endpoint: ${sourceBranchId}`);
    }
    if (target === undefined) {
      throw new Error(`Unknown asset group constraint endpoint: ${targetBranchId}`);
    }
    sourceByEdge[edgeIndex] = source;
    targetByEdge[edgeIndex] = target;
    outgoingCount[source] = outgoingCount[source]! + 1;
    incomingCount[target] = incomingCount[target]! + 1;
  }

  const offsets = (counts: Int32Array) => {
    const result = new Int32Array(groupCount + 1);
    for (let index = 0; index < groupCount; index++) {
      result[index + 1] = result[index]! + counts[index]!;
    }
    return result;
  };
  const outgoingOffset = offsets(outgoingCount);
  const incomingOffset = offsets(incomingCount);
  const outgoingCursor = outgoingOffset.slice(0, groupCount);
  const incomingCursor = incomingOffset.slice(0, groupCount);
  const outgoing = new Int32Array(edgeCount);
  const incoming = new Int32Array(edgeCount);
  for (let edgeIndex = 0; edgeIndex < edgeCount; edgeIndex++) {
    const source = sourceByEdge[edgeIndex]!;
    const target = targetByEdge[edgeIndex]!;
    const outgoingIndex = outgoingCursor[source]!;
    const incomingIndex = incomingCursor[target]!;
    outgoing[outgoingIndex] = target;
    incoming[incomingIndex] = source;
    outgoingCursor[source] = outgoingIndex + 1;
    incomingCursor[target] = incomingIndex + 1;
  }

  const visited = new Uint8Array(groupCount);
  const finishOrder = new Int32Array(groupCount);
  const stackNode = new Int32Array(groupCount);
  const stackEdge = new Int32Array(groupCount);
  let finishedCount = 0;
  for (let start = 0; start < groupCount; start++) {
    if (visited[start]) {
      continue;
    }
    let stackSize = 1;
    stackNode[0] = start;
    stackEdge[0] = outgoingOffset[start]!;
    visited[start] = 1;
    while (stackSize) {
      const frame = stackSize - 1;
      const node = stackNode[frame]!;
      const nextEdge = stackEdge[frame]!;
      if (nextEdge < outgoingOffset[node + 1]!) {
        const neighbor = outgoing[nextEdge]!;
        stackEdge[frame] = nextEdge + 1;
        if (!visited[neighbor]) {
          visited[neighbor] = 1;
          stackNode[stackSize] = neighbor;
          stackEdge[stackSize] = outgoingOffset[neighbor]!;
          stackSize++;
        }
      } else {
        finishOrder[finishedCount++] = node;
        stackSize--;
      }
    }
  }

  const componentByIndex = new Int32Array(groupCount);
  componentByIndex.fill(-1);
  const componentIdIndex = new Int32Array(groupCount);
  let componentCount = 0;
  for (let orderIndex = finishedCount - 1; orderIndex >= 0; orderIndex--) {
    const start = finishOrder[orderIndex]!;
    if (componentByIndex[start] !== -1) {
      continue;
    }
    let stackSize = 1;
    stackNode[0] = start;
    componentByIndex[start] = componentCount;
    let minimumIndex = start;
    while (stackSize) {
      const node = stackNode[--stackSize]!;
      minimumIndex = Math.min(minimumIndex, node);
      for (
        let edgeIndex = incomingOffset[node]!;
        edgeIndex < incomingOffset[node + 1]!;
        edgeIndex++
      ) {
        const neighbor = incoming[edgeIndex]!;
        if (componentByIndex[neighbor] === -1) {
          componentByIndex[neighbor] = componentCount;
          stackNode[stackSize++] = neighbor;
        }
      }
    }
    componentIdIndex[componentCount++] = minimumIndex;
  }
  return {componentByIndex, componentIdIndex, componentCount, sourceByEdge, targetByEdge};
};

const solveAssetGroupConstraintsNumeric = (
  {
    direction,
    ranksep,
    trailingGroupPadding,
    groups,
    parentById,
    constraints,
  }: AssetGroupConstraintInput,
  columns?: ConstraintColumns,
) => {
  const ids = Object.keys(groups).sort();
  const indexById = new Map<string, number>();
  for (let index = 0; index < ids.length; index++) {
    indexById.set(ids[index]!, index);
  }
  const {componentByIndex, componentIdIndex, componentCount, sourceByEdge, targetByEdge} =
    buildConstraintComponents(ids, indexById, constraints, columns);
  const groupCount = ids.length;
  const constraintCount = columns?.count ?? constraints.length;
  const zeroNode = 0;
  const moveNode = (component: number) => 1 + component;
  const endNode = (groupIndex: number) => 1 + componentCount + groupIndex;
  const nodeCount = 1 + componentCount + groupCount;
  const edgeCapacity = groupCount * 4 + constraintCount;
  const edgeFrom = new Int32Array(edgeCapacity);
  const edgeTo = new Int32Array(edgeCapacity);
  const edgeWeight = new Float64Array(edgeCapacity);
  let edgeCount = 0;
  const addEdge = (from: number, to: number, weight: number) => {
    if (!Number.isFinite(weight)) {
      throw new Error('Non-finite asset group constraint');
    }
    edgeFrom[edgeCount] = from;
    edgeTo[edgeCount] = to;
    edgeWeight[edgeCount] = weight;
    edgeCount++;
  };

  for (let index = 0; index < groupCount; index++) {
    const id = ids[index]!;
    const componentMove = moveNode(componentByIndex[index]!);
    addEdge(zeroNode, componentMove, 0);
    addEdge(componentMove, endNode(index), primaryEnd(groups[id]!.bounds, direction));

    const parentId = parentById[id];
    if (parentId === undefined) {
      throw new Error(`Missing visible asset group parent: undefined`);
    }
    if (parentId !== null) {
      const parentIndex = indexById.get(parentId);
      if (parentIndex === undefined) {
        throw new Error(`Missing visible asset group parent: ${parentId}`);
      }
      const parentMove = moveNode(componentByIndex[parentIndex]!);
      if (parentMove !== componentMove) {
        addEdge(parentMove, componentMove, 0);
      }
      addEdge(endNode(index), endNode(parentIndex), trailingGroupPadding);
    }
  }

  for (let index = 0; index < constraintCount; index++) {
    const constraint = columns ? undefined : constraints[index]!;
    const sourceComponent = componentByIndex[sourceByEdge[index]!]!;
    const targetComponent = componentByIndex[targetByEdge[index]!]!;
    if (sourceComponent === targetComponent) {
      continue;
    }
    const sourceUsesGroupEnd = columns
      ? columns.sourceUsesGroupEnd[index] === 1
      : constraint!.sourceUsesGroupEnd;
    const sourceBaseExit = columns ? columns.sourceBaseExit[index]! : constraint!.sourceBaseExit;
    const targetBaseEntry = columns ? columns.targetBaseEntry[index]! : constraint!.targetBaseEntry;
    if (sourceUsesGroupEnd) {
      addEdge(endNode(sourceByEdge[index]!), moveNode(targetComponent), ranksep - targetBaseEntry);
    } else {
      addEdge(
        moveNode(sourceComponent),
        moveNode(targetComponent),
        sourceBaseExit + ranksep - targetBaseEntry,
      );
    }
  }

  const outgoingCount = new Int32Array(nodeCount);
  const indegree = new Int32Array(nodeCount);
  for (let index = 0; index < edgeCount; index++) {
    const from = edgeFrom[index]!;
    const to = edgeTo[index]!;
    outgoingCount[from] = outgoingCount[from]! + 1;
    indegree[to] = indegree[to]! + 1;
  }
  const outgoingOffset = new Int32Array(nodeCount + 1);
  for (let index = 0; index < nodeCount; index++) {
    outgoingOffset[index + 1] = outgoingOffset[index]! + outgoingCount[index]!;
  }
  const cursor = outgoingOffset.slice(0, nodeCount);
  const targetByAdjacency = new Int32Array(edgeCount);
  const weightByAdjacency = new Float64Array(edgeCount);
  for (let index = 0; index < edgeCount; index++) {
    const from = edgeFrom[index]!;
    const adjacencyIndex = cursor[from]!;
    cursor[from] = adjacencyIndex + 1;
    targetByAdjacency[adjacencyIndex] = edgeTo[index]!;
    weightByAdjacency[adjacencyIndex] = edgeWeight[index]!;
  }

  const ready = new Int32Array(nodeCount);
  let readyCount = 0;
  for (let node = 0; node < nodeCount; node++) {
    if (indegree[node] === 0) {
      ready[readyCount++] = node;
    }
  }
  const distance = new Float64Array(nodeCount);
  distance.fill(Number.NEGATIVE_INFINITY);
  distance[zeroNode] = 0;
  let visitedCount = 0;
  while (readyCount) {
    const node = ready[--readyCount]!;
    visitedCount++;
    const fromDistance = distance[node]!;
    for (
      let edgeIndex = outgoingOffset[node]!;
      edgeIndex < outgoingOffset[node + 1]!;
      edgeIndex++
    ) {
      const target = targetByAdjacency[edgeIndex]!;
      if (Number.isFinite(fromDistance)) {
        const candidate = fromDistance + weightByAdjacency[edgeIndex]!;
        if (!Number.isFinite(candidate)) {
          throw new Error('Non-finite asset group constraint solution');
        }
        distance[target] = Math.max(distance[target]!, candidate);
      }
      const nextIndegree = indegree[target]! - 1;
      indegree[target] = nextIndegree;
      if (nextIndegree === 0) {
        ready[readyCount++] = target;
      }
    }
  }
  if (visitedCount !== nodeCount) {
    throw new Error('Cyclic asset group constraint graph after SCC collapse');
  }

  const shiftByIndex = new Float64Array(groupCount);
  const endByIndex = new Float64Array(groupCount);
  for (let index = 0; index < groupCount; index++) {
    const id = ids[index]!;
    const component = componentByIndex[index]!;
    const shift = distance[moveNode(component)]!;
    const end = distance[endNode(index)]!;
    if (!Number.isFinite(shift) || !Number.isFinite(end)) {
      throw new Error('Non-finite asset group constraint solution');
    }
    shiftByIndex[index] = shift;
    endByIndex[index] = end;
  }
  return {ids, indexById, shiftByIndex, endByIndex, componentByIndex, componentIdIndex};
};

export const solveAssetGroupConstraints = (
  input: AssetGroupConstraintInput,
): AssetGroupConstraintSolution => {
  const solution = solveAssetGroupConstraintsNumeric(input);
  const shiftByGroupId: Record<string, number> = {};
  const endByGroupId: Record<string, number> = {};
  const componentByGroupId: Record<string, string> = {};
  for (let index = 0; index < solution.ids.length; index++) {
    const id = solution.ids[index]!;
    const component = solution.componentByIndex[index]!;
    shiftByGroupId[id] = solution.shiftByIndex[index]!;
    endByGroupId[id] = solution.endByIndex[index]!;
    componentByGroupId[id] = solution.ids[solution.componentIdIndex[component]!]!;
  }
  return {shiftByGroupId, endByGroupId, componentByGroupId};
};

const pointPrimary = (point: {x: number; y: number}, direction: RoutingDirection) =>
  direction === 'horizontal' ? point.x : point.y;

const translatePoint = (
  point: {x: number; y: number},
  amount: number,
  direction: RoutingDirection,
) => {
  const translatedPrimary = pointPrimary(point, direction) + amount;
  if (!Number.isFinite(translatedPrimary)) {
    throw new Error('Non-finite asset group routed edge endpoint');
  }
  return direction === 'horizontal'
    ? {x: translatedPrimary, y: point.y}
    : {x: point.x, y: translatedPrimary};
};

const translateBounds = (bounds: IBounds, amount: number, direction: RoutingDirection): IBounds => {
  const translatedPrimary = primaryStart(bounds, direction) + amount;
  if (!Number.isFinite(translatedPrimary)) {
    throw new Error('Non-finite routed asset bounds');
  }
  return direction === 'horizontal'
    ? {x: translatedPrimary, y: bounds.y, width: bounds.width, height: bounds.height}
    : {x: bounds.x, y: translatedPrimary, width: bounds.width, height: bounds.height};
};

type ConstraintColumns = {
  count: number;
  sourceBranchIds: string[];
  targetBranchIds: string[];
  sourceUsesGroupEnd: Uint8Array;
  sourceBaseExit: Float64Array;
  targetBaseEntry: Float64Array;
};

const validBounds = (value: IBounds) =>
  Number.isFinite(value.x) &&
  Number.isFinite(value.y) &&
  Number.isFinite(value.width) &&
  Number.isFinite(value.height) &&
  value.width >= 0 &&
  value.height >= 0;

const assertValidOutputCorridor = (
  edge: RoutingLayoutEdge,
  direction: RoutingDirection,
  ranksep: number,
) => {
  const sourceBoundary = edge.sourceBoundary!;
  const targetBoundary = edge.targetBoundary!;
  if (
    !Number.isFinite(sourceBoundary) ||
    !Number.isFinite(targetBoundary) ||
    pointPrimary(edge.from, direction) > sourceBoundary ||
    sourceBoundary + ranksep > targetBoundary ||
    targetBoundary > pointPrimary(edge.to, direction)
  ) {
    throw new Error('Invalid asset group routed edge corridor');
  }
};

const validateInputCorridors = (layout: RoutingLayout, options: ApplyAssetGroupRoutingOptions) => {
  if (
    !Number.isFinite(layout.width) ||
    !Number.isFinite(layout.height) ||
    layout.width <= 0 ||
    layout.height <= 0
  ) {
    return false;
  }
  for (const id in layout.groups) {
    if (!Object.prototype.hasOwnProperty.call(layout.groups, id)) {
      continue;
    }
    const group = layout.groups[id];
    if (!group || !validBounds(group.bounds)) {
      return false;
    }
  }
  for (const id in layout.nodes) {
    if (!Object.prototype.hasOwnProperty.call(layout.nodes, id)) {
      continue;
    }
    const node = layout.nodes[id];
    if (!node || !validBounds(node.bounds)) {
      return false;
    }
  }
  for (const edge of layout.edges) {
    const hasSourceBoundary = edge.sourceBoundary !== undefined;
    const hasTargetBoundary = edge.targetBoundary !== undefined;
    if (hasSourceBoundary !== hasTargetBoundary) {
      return false;
    }
    if (
      !Number.isFinite(edge.from.x) ||
      !Number.isFinite(edge.from.y) ||
      !Number.isFinite(edge.to.x) ||
      !Number.isFinite(edge.to.y)
    ) {
      return false;
    }
    if (!hasSourceBoundary) {
      continue;
    }
    const sourceBoundary = edge.sourceBoundary!;
    const targetBoundary = edge.targetBoundary!;
    const sourceEndpoint = pointPrimary(edge.from, options.direction);
    const targetEndpoint = pointPrimary(edge.to, options.direction);
    if (
      !Number.isFinite(sourceEndpoint) ||
      !Number.isFinite(targetEndpoint) ||
      !Number.isFinite(sourceBoundary) ||
      !Number.isFinite(targetBoundary) ||
      sourceEndpoint > sourceBoundary ||
      sourceBoundary + options.ranksep > targetBoundary ||
      targetBoundary > targetEndpoint
    ) {
      return false;
    }
  }
  return true;
};

const applyAssetGroupLineageRoutingImpl = <T extends RoutingLayout>(
  layout: T,
  options: ApplyAssetGroupRoutingOptions,
): T => {
  if (
    (options.direction !== 'horizontal' && options.direction !== 'vertical') ||
    !Number.isFinite(options.ranksep) ||
    options.ranksep < 0 ||
    !Number.isFinite(options.trailingGroupPadding) ||
    options.trailingGroupPadding < 0 ||
    !Number.isFinite(options.margin) ||
    options.margin < 0
  ) {
    throw new Error('Invalid asset group routing options');
  }

  let hasNestedGroups = false;
  for (const id in options.groupParentById) {
    if (options.groupParentById[id] !== null) {
      hasNestedGroups = true;
      break;
    }
  }
  const ancestry = hasNestedGroups ? buildGroupAncestryIndex(options.groupParentById) : undefined;
  const constraintIndexByEdge = new Int32Array(layout.edges.length);
  constraintIndexByEdge.fill(-1);
  const constraintColumns: ConstraintColumns = {
    count: 0,
    sourceBranchIds: [],
    targetBranchIds: [],
    sourceUsesGroupEnd: new Uint8Array(layout.edges.length),
    sourceBaseExit: new Float64Array(layout.edges.length),
    targetBaseEntry: new Float64Array(layout.edges.length),
  };
  let hasPartiallyGroupedEdge = false;

  layout.edges.forEach((edge, index) => {
    const sourceEndpointGroupId = options.endpointGroupById[edge.fromId];
    const targetEndpointGroupId = options.endpointGroupById[edge.toId];
    if (!!sourceEndpointGroupId !== !!targetEndpointGroupId) {
      hasPartiallyGroupedEdge = true;
    }
    if (
      !sourceEndpointGroupId ||
      !targetEndpointGroupId ||
      sourceEndpointGroupId === targetEndpointGroupId
    ) {
      return;
    }

    const lca =
      ancestry?.lowestCommonAncestor(sourceEndpointGroupId, targetEndpointGroupId) ?? null;
    const sourceBranchId = ancestry
      ? ancestry.branchBelow(sourceEndpointGroupId, lca)
      : sourceEndpointGroupId;
    const targetBranchId = ancestry
      ? ancestry.branchBelow(targetEndpointGroupId, lca)
      : targetEndpointGroupId;
    if (!sourceBranchId || !targetBranchId || sourceBranchId === targetBranchId) {
      return;
    }
    const sourceGroup = layout.groups[sourceBranchId];
    const targetGroup = layout.groups[targetBranchId];
    if (!sourceGroup || !targetGroup) {
      throw new Error('Missing asset group routing branch');
    }

    const sourceUsesGroupEnd = sourceGroup.expanded || edge.fromId !== sourceBranchId;
    const targetUsesGroupStart = targetGroup.expanded || edge.toId !== targetBranchId;
    const constraintIndex = constraintColumns.count++;
    constraintIndexByEdge[index] = constraintIndex;
    constraintColumns.sourceBranchIds.push(sourceBranchId);
    constraintColumns.targetBranchIds.push(targetBranchId);
    constraintColumns.sourceUsesGroupEnd[constraintIndex] = sourceUsesGroupEnd ? 1 : 0;
    constraintColumns.sourceBaseExit[constraintIndex] = sourceUsesGroupEnd
      ? primaryEnd(sourceGroup.bounds, options.direction)
      : pointPrimary(edge.from, options.direction);
    constraintColumns.targetBaseEntry[constraintIndex] = targetUsesGroupStart
      ? primaryStart(targetGroup.bounds, options.direction)
      : pointPrimary(edge.to, options.direction);
  });

  const solution = solveAssetGroupConstraintsNumeric(
    {
      direction: options.direction,
      ranksep: options.ranksep,
      trailingGroupPadding: options.trailingGroupPadding,
      groups: layout.groups,
      parentById: options.groupParentById,
      constraints: [],
    },
    constraintColumns,
  );
  const requireSolutionIndex = (groupId: string) => {
    const index = solution.indexById.get(groupId);
    if (index === undefined) {
      throw new Error('Missing solved asset group geometry');
    }
    return index;
  };
  const shiftForGroup = (groupId: string) => solution.shiftByIndex[requireSolutionIndex(groupId)]!;

  if (hasPartiallyGroupedEdge) {
    for (const edge of layout.edges) {
      const sourceEndpointGroupId = options.endpointGroupById[edge.fromId];
      const targetEndpointGroupId = options.endpointGroupById[edge.toId];
      if (!!sourceEndpointGroupId === !!targetEndpointGroupId) {
        continue;
      }
      const sourceShift = sourceEndpointGroupId ? shiftForGroup(sourceEndpointGroupId) : 0;
      const targetShift = targetEndpointGroupId ? shiftForGroup(targetEndpointGroupId) : 0;
      if (sourceShift !== targetShift) {
        throw new Error('Cannot partially translate an edge outside asset groups');
      }
    }
  }

  const groups: RoutingLayout['groups'] = {};
  for (const id in layout.groups) {
    if (!Object.prototype.hasOwnProperty.call(layout.groups, id)) {
      continue;
    }
    const group = layout.groups[id]!;
    const solutionIndex = requireSolutionIndex(id);
    const shift = solution.shiftByIndex[solutionIndex]!;
    const end = solution.endByIndex[solutionIndex]!;
    const bounds = group.bounds;
    const translatedStart = primaryStart(bounds, options.direction) + shift;
    const translatedSize = end - translatedStart;
    if (
      !Number.isFinite(translatedStart) ||
      !Number.isFinite(translatedSize) ||
      translatedSize < 0
    ) {
      throw new Error('Invalid routed asset group bounds');
    }
    const translatedBounds =
      options.direction === 'horizontal'
        ? {x: translatedStart, y: bounds.y, width: translatedSize, height: bounds.height}
        : {x: bounds.x, y: translatedStart, width: bounds.width, height: translatedSize};
    groups[id] = {...group, bounds: translatedBounds};
  }

  const nodes: RoutingLayout['nodes'] = {};
  for (const id in layout.nodes) {
    if (!Object.prototype.hasOwnProperty.call(layout.nodes, id)) {
      continue;
    }
    const node = layout.nodes[id]!;
    const ownerGroupId = options.ownerGroupByNodeId[id];
    const shift =
      ownerGroupId === null || ownerGroupId === undefined ? 0 : shiftForGroup(ownerGroupId);
    const bounds = translateBounds(node.bounds, shift, options.direction);
    nodes[id] = {...node, bounds};
  }

  const edges = layout.edges.map((edge, index) => {
    const sourceEndpointGroupId = options.endpointGroupById[edge.fromId];
    const targetEndpointGroupId = options.endpointGroupById[edge.toId];
    const sourceShift = sourceEndpointGroupId ? shiftForGroup(sourceEndpointGroupId) : 0;
    const targetShift = targetEndpointGroupId ? shiftForGroup(targetEndpointGroupId) : 0;
    const from = translatePoint(edge.from, sourceShift, options.direction);
    const to = translatePoint(edge.to, targetShift, options.direction);
    const translated = {...edge, from, to};
    delete translated.sourceBoundary;
    delete translated.targetBoundary;
    const constraintIndex = constraintIndexByEdge[index]!;
    if (
      constraintIndex !== -1 &&
      solution.componentByIndex[
        requireSolutionIndex(constraintColumns.sourceBranchIds[constraintIndex]!)
      ] !==
        solution.componentByIndex[
          requireSolutionIndex(constraintColumns.targetBranchIds[constraintIndex]!)
        ]
    ) {
      const sourceBranchIndex = requireSolutionIndex(
        constraintColumns.sourceBranchIds[constraintIndex]!,
      );
      const sourceBranchShift = solution.shiftByIndex[sourceBranchIndex]!;
      const targetBranchShift = shiftForGroup(constraintColumns.targetBranchIds[constraintIndex]!);
      translated.sourceBoundary = constraintColumns.sourceUsesGroupEnd[constraintIndex]
        ? solution.endByIndex[sourceBranchIndex]!
        : constraintColumns.sourceBaseExit[constraintIndex]! + sourceBranchShift;
      translated.targetBoundary =
        constraintColumns.targetBaseEntry[constraintIndex]! + targetBranchShift;
      assertValidOutputCorridor(translated, options.direction, options.ranksep);
    }
    return translated;
  });

  let maximumForwardEnd: number | undefined;
  for (const id in groups) {
    const group = groups[id];
    if (group) {
      const end = primaryEnd(group.bounds, options.direction);
      maximumForwardEnd = maximumForwardEnd === undefined ? end : Math.max(maximumForwardEnd, end);
    }
  }
  for (const id in nodes) {
    const node = nodes[id];
    if (node) {
      const end = primaryEnd(node.bounds, options.direction);
      maximumForwardEnd = maximumForwardEnd === undefined ? end : Math.max(maximumForwardEnd, end);
    }
  }
  const forwardEnd = maximumForwardEnd ?? 0;
  const result = {
    ...layout,
    width:
      options.direction === 'horizontal'
        ? Math.max(layout.width, forwardEnd + options.margin)
        : layout.width,
    height:
      options.direction === 'vertical'
        ? Math.max(layout.height, forwardEnd + options.margin)
        : layout.height,
    nodes,
    groups,
    edges,
  } as T;
  if (
    !Number.isFinite(result.width) ||
    !Number.isFinite(result.height) ||
    result.width <= 0 ||
    result.height <= 0
  ) {
    throw new Error('Invalid routed asset graph canvas');
  }
  return result;
};

export const applyAssetGroupLineageRouting = <T extends RoutingLayout>(
  layout: T,
  options: ApplyAssetGroupRoutingOptions,
): T => {
  try {
    if (!validateInputCorridors(layout, options)) {
      return layout;
    }
    return applyAssetGroupLineageRoutingImpl(layout, options);
  } catch {
    return layout;
  }
};
