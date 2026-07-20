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

const compareStrings = (left: string, right: string) => (left < right ? -1 : left > right ? 1 : 0);

export type GroupAncestryIndex = {
  lowestCommonAncestor: (a: string, b: string) => string | null;
  branchBelow: (groupId: string, ancestorId: string | null) => string | null;
};

export const buildGroupAncestryIndex = (parentById: GroupParentById): GroupAncestryIndex => {
  const ids = Object.keys(parentById).sort();
  const indexById = new Map(ids.map((id, index) => [id, index]));
  const groupCount = ids.length;

  const parent = new Int32Array(groupCount);
  parent.fill(-1);
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

  const requireIndex = (id: string) => {
    const index = indexById.get(id);
    if (index === undefined) {
      throw new Error(`Unknown visible asset group: ${id}`);
    }
    return index;
  };

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
  constraints: BranchConstraint[],
): Record<string, string> => {
  const idSet = new Set(ids);
  const adjacencySets = new Map(ids.map((id) => [id, new Set<string>()]));
  const reverseSets = new Map(ids.map((id) => [id, new Set<string>()]));

  for (const constraint of constraints) {
    if (!idSet.has(constraint.sourceBranchId)) {
      throw new Error(`Unknown asset group constraint endpoint: ${constraint.sourceBranchId}`);
    }
    if (!idSet.has(constraint.targetBranchId)) {
      throw new Error(`Unknown asset group constraint endpoint: ${constraint.targetBranchId}`);
    }
    adjacencySets.get(constraint.sourceBranchId)!.add(constraint.targetBranchId);
    reverseSets.get(constraint.targetBranchId)!.add(constraint.sourceBranchId);
  }
  const adjacency = new Map(ids.map((id) => [id, [...adjacencySets.get(id)!].sort()] as const));
  const reverse = new Map(ids.map((id) => [id, [...reverseSets.get(id)!].sort()] as const));

  const visited = new Set<string>();
  const finishOrder: string[] = [];
  for (const start of ids) {
    if (visited.has(start)) {
      continue;
    }
    visited.add(start);
    const frames = [{id: start, next: 0}];
    while (frames.length) {
      const frame = frames[frames.length - 1]!;
      const neighbors = adjacency.get(frame.id)!;
      if (frame.next < neighbors.length) {
        const neighbor = neighbors[frame.next++]!;
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          frames.push({id: neighbor, next: 0});
        }
      } else {
        finishOrder.push(frame.id);
        frames.pop();
      }
    }
  }

  const assigned = new Set<string>();
  const components: string[][] = [];
  for (let index = finishOrder.length - 1; index >= 0; index--) {
    const start = finishOrder[index]!;
    if (assigned.has(start)) {
      continue;
    }
    assigned.add(start);
    const component: string[] = [];
    const stack = [start];
    while (stack.length) {
      const id = stack.pop()!;
      component.push(id);
      for (const neighbor of reverse.get(id)!) {
        if (!assigned.has(neighbor)) {
          assigned.add(neighbor);
          stack.push(neighbor);
        }
      }
    }
    component.sort();
    components.push(component);
  }
  components.sort((left, right) => compareStrings(left[0]!, right[0]!));

  const componentByGroupId: Record<string, string> = {};
  for (const component of components) {
    const componentId = component[0]!;
    for (const id of component) {
      componentByGroupId[id] = componentId;
    }
  }
  return componentByGroupId;
};

class StringMinHeap {
  private values: string[] = [];

  public push(value: string) {
    this.values.push(value);
    let index = this.values.length - 1;
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (compareStrings(this.values[parent]!, value) <= 0) {
        break;
      }
      this.values[index] = this.values[parent]!;
      index = parent;
    }
    this.values[index] = value;
  }

  public pop() {
    if (this.values.length === 0) {
      return undefined;
    }
    const minimum = this.values[0]!;
    const last = this.values.pop()!;
    if (this.values.length === 0) {
      return minimum;
    }

    let index = 0;
    while (true) {
      const left = index * 2 + 1;
      if (left >= this.values.length) {
        break;
      }
      const right = left + 1;
      const child =
        right < this.values.length && compareStrings(this.values[right]!, this.values[left]!) < 0
          ? right
          : left;
      if (compareStrings(this.values[child]!, last) >= 0) {
        break;
      }
      this.values[index] = this.values[child]!;
      index = child;
    }
    this.values[index] = last;
    return minimum;
  }
}

type WeightedEdge = {from: string; to: string; weight: number};

export const solveAssetGroupConstraints = ({
  direction,
  ranksep,
  trailingGroupPadding,
  groups,
  parentById,
  constraints,
}: AssetGroupConstraintInput): AssetGroupConstraintSolution => {
  const ids = Object.keys(groups).sort();
  const idSet = new Set(ids);
  const componentByGroupId = buildConstraintComponents(ids, constraints);
  const componentIds = [...new Set(ids.map((id) => componentByGroupId[id]!))];
  const zeroNode = '$zero';
  const moveNode = (componentId: string) => `move:${componentId}`;
  const endNode = (groupId: string) => `end:${groupId}`;
  const nodes = new Set<string>([zeroNode]);
  for (const componentId of componentIds) {
    nodes.add(moveNode(componentId));
  }
  for (const id of ids) {
    nodes.add(endNode(id));
  }

  const edgeWeightByNodes = new Map<string, Map<string, number>>();
  const addEdge = (from: string, to: string, weight: number) => {
    if (!Number.isFinite(weight)) {
      throw new Error('Non-finite asset group constraint');
    }
    let weightByTarget = edgeWeightByNodes.get(from);
    if (!weightByTarget) {
      weightByTarget = new Map();
      edgeWeightByNodes.set(from, weightByTarget);
    }
    const previousWeight = weightByTarget.get(to);
    if (previousWeight === undefined || weight > previousWeight) {
      weightByTarget.set(to, weight);
    }
  };

  for (const id of ids) {
    const componentMove = moveNode(componentByGroupId[id]!);
    addEdge(zeroNode, componentMove, 0);
    addEdge(componentMove, endNode(id), primaryEnd(groups[id]!.bounds, direction));

    const parentId = parentById[id];
    if (parentId === undefined) {
      throw new Error(`Missing visible asset group parent: undefined`);
    }
    if (parentId !== null) {
      if (!idSet.has(parentId)) {
        throw new Error(`Missing visible asset group parent: ${parentId}`);
      }
      const parentMove = moveNode(componentByGroupId[parentId]!);
      if (parentMove !== componentMove) {
        addEdge(parentMove, componentMove, 0);
      }
      addEdge(endNode(id), endNode(parentId), trailingGroupPadding);
    }
  }

  for (const constraint of constraints) {
    const sourceComponent = componentByGroupId[constraint.sourceBranchId]!;
    const targetComponent = componentByGroupId[constraint.targetBranchId]!;
    if (sourceComponent === targetComponent) {
      continue;
    }
    if (constraint.sourceUsesGroupEnd) {
      addEdge(
        endNode(constraint.sourceBranchId),
        moveNode(targetComponent),
        ranksep - constraint.targetBaseEntry,
      );
    } else {
      addEdge(
        moveNode(sourceComponent),
        moveNode(targetComponent),
        constraint.sourceBaseExit + ranksep - constraint.targetBaseEntry,
      );
    }
  }

  const edges = [...edgeWeightByNodes].flatMap(([from, weightByTarget]) =>
    [...weightByTarget].map(([to, weight]) => ({from, to, weight})),
  );
  edges.sort(
    (left, right) =>
      compareStrings(left.from, right.from) ||
      compareStrings(left.to, right.to) ||
      left.weight - right.weight,
  );
  const adjacency = new Map([...nodes].map((node) => [node, [] as WeightedEdge[]]));
  const indegree = new Map([...nodes].map((node) => [node, 0]));
  for (const edge of edges) {
    adjacency.get(edge.from)!.push(edge);
    indegree.set(edge.to, indegree.get(edge.to)! + 1);
  }

  const ready = new StringMinHeap();
  for (const node of nodes) {
    if (indegree.get(node) === 0) {
      ready.push(node);
    }
  }
  const distance = new Map([...nodes].map((node) => [node, Number.NEGATIVE_INFINITY]));
  distance.set(zeroNode, 0);
  let visitedCount = 0;
  for (let node = ready.pop(); node !== undefined; node = ready.pop()) {
    visitedCount++;
    const fromDistance = distance.get(node)!;
    for (const edge of adjacency.get(node)!) {
      if (Number.isFinite(fromDistance)) {
        distance.set(edge.to, Math.max(distance.get(edge.to)!, fromDistance + edge.weight));
      }
      const nextIndegree = indegree.get(edge.to)! - 1;
      indegree.set(edge.to, nextIndegree);
      if (nextIndegree === 0) {
        ready.push(edge.to);
      }
    }
  }
  if (visitedCount !== nodes.size) {
    throw new Error('Cyclic asset group constraint graph after SCC collapse');
  }

  const shiftByGroupId: Record<string, number> = {};
  const endByGroupId: Record<string, number> = {};
  for (const id of ids) {
    const shift = distance.get(moveNode(componentByGroupId[id]!));
    const end = distance.get(endNode(id));
    shiftByGroupId[id] = Number.isFinite(shift) ? shift! : 0;
    endByGroupId[id] = Number.isFinite(end) ? end! : primaryEnd(groups[id]!.bounds, direction);
  }
  return {shiftByGroupId, endByGroupId, componentByGroupId};
};

const pointPrimary = (point: {x: number; y: number}, direction: RoutingDirection) =>
  direction === 'horizontal' ? point.x : point.y;

const translatePoint = (
  point: {x: number; y: number},
  amount: number,
  direction: RoutingDirection,
) =>
  direction === 'horizontal' ? {...point, x: point.x + amount} : {...point, y: point.y + amount};

const translateBounds = (bounds: IBounds, amount: number, direction: RoutingDirection): IBounds =>
  direction === 'horizontal'
    ? {...bounds, x: bounds.x + amount}
    : {...bounds, y: bounds.y + amount};

const withForwardEnd = (bounds: IBounds, end: number, direction: RoutingDirection): IBounds =>
  direction === 'horizontal'
    ? {...bounds, width: end - bounds.x}
    : {...bounds, height: end - bounds.y};

type InternalEdgeRouteInfo = EdgeRouteInfo;

const validBounds = (value: IBounds) =>
  Number.isFinite(value.x) &&
  Number.isFinite(value.y) &&
  Number.isFinite(value.width) &&
  Number.isFinite(value.height) &&
  value.width >= 0 &&
  value.height >= 0;

const sameKeys = (left: Record<string, unknown>, right: Record<string, unknown>) => {
  const leftKeys = Object.keys(left).sort();
  const rightKeys = Object.keys(right).sort();
  return (
    leftKeys.length === rightKeys.length && leftKeys.every((key, index) => key === rightKeys[index])
  );
};

const validateInputCorridors = (layout: RoutingLayout, options: ApplyAssetGroupRoutingOptions) => {
  for (const edge of layout.edges) {
    const hasSourceBoundary = edge.sourceBoundary !== undefined;
    const hasTargetBoundary = edge.targetBoundary !== undefined;
    if (hasSourceBoundary !== hasTargetBoundary) {
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

const validateRoutingResult = (
  original: RoutingLayout,
  result: RoutingLayout,
  options: ApplyAssetGroupRoutingOptions,
) => {
  if (
    !Number.isFinite(original.width) ||
    !Number.isFinite(original.height) ||
    original.width <= 0 ||
    original.height <= 0 ||
    !Number.isFinite(result.width) ||
    !Number.isFinite(result.height) ||
    result.width <= 0 ||
    result.height <= 0 ||
    !sameKeys(original.nodes, result.nodes) ||
    !sameKeys(original.groups, result.groups) ||
    original.edges.length !== result.edges.length
  ) {
    return false;
  }

  for (const id of Object.keys(original.groups)) {
    const before = original.groups[id];
    const after = result.groups[id];
    if (!before || !after || !validBounds(before.bounds) || !validBounds(after.bounds)) {
      return false;
    }
    if (
      (options.direction === 'horizontal' &&
        (before.bounds.y !== after.bounds.y || before.bounds.height !== after.bounds.height)) ||
      (options.direction === 'vertical' &&
        (before.bounds.x !== after.bounds.x || before.bounds.width !== after.bounds.width))
    ) {
      return false;
    }
  }

  for (const id of Object.keys(original.nodes)) {
    const before = original.nodes[id];
    const after = result.nodes[id];
    if (!before || !after || !validBounds(before.bounds) || !validBounds(after.bounds)) {
      return false;
    }
    if (
      (options.direction === 'horizontal' &&
        (before.bounds.y !== after.bounds.y || before.bounds.height !== after.bounds.height)) ||
      (options.direction === 'vertical' &&
        (before.bounds.x !== after.bounds.x || before.bounds.width !== after.bounds.width))
    ) {
      return false;
    }
  }

  for (let index = 0; index < result.edges.length; index++) {
    const before = original.edges[index];
    const edge = result.edges[index];
    if (!before || !edge || before.fromId !== edge.fromId || before.toId !== edge.toId) {
      return false;
    }
    const originalHasSourceBoundary = before.sourceBoundary !== undefined;
    const originalHasTargetBoundary = before.targetBoundary !== undefined;
    if (
      originalHasSourceBoundary !== originalHasTargetBoundary ||
      (originalHasSourceBoundary &&
        (!Number.isFinite(before.sourceBoundary) || !Number.isFinite(before.targetBoundary)))
    ) {
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
    const hasSourceBoundary = edge.sourceBoundary !== undefined;
    const hasTargetBoundary = edge.targetBoundary !== undefined;
    if (hasSourceBoundary !== hasTargetBoundary) {
      return false;
    }
    if (hasSourceBoundary) {
      const sourceBoundary = edge.sourceBoundary!;
      const targetBoundary = edge.targetBoundary!;
      if (
        !Number.isFinite(sourceBoundary) ||
        !Number.isFinite(targetBoundary) ||
        pointPrimary(edge.from, options.direction) > sourceBoundary ||
        sourceBoundary + options.ranksep > targetBoundary ||
        targetBoundary > pointPrimary(edge.to, options.direction)
      ) {
        return false;
      }
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

  const ancestry = buildGroupAncestryIndex(options.groupParentById);
  const routeInfoByEdge = new Map<number, InternalEdgeRouteInfo>();
  const constraints: BranchConstraint[] = [];

  layout.edges.forEach((edge, index) => {
    const sourceEndpointGroupId = options.endpointGroupById[edge.fromId];
    const targetEndpointGroupId = options.endpointGroupById[edge.toId];
    if (
      !sourceEndpointGroupId ||
      !targetEndpointGroupId ||
      sourceEndpointGroupId === targetEndpointGroupId
    ) {
      return;
    }

    const lca = ancestry.lowestCommonAncestor(sourceEndpointGroupId, targetEndpointGroupId);
    const sourceBranchId = ancestry.branchBelow(sourceEndpointGroupId, lca);
    const targetBranchId = ancestry.branchBelow(targetEndpointGroupId, lca);
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
    const routeInfo: InternalEdgeRouteInfo = {
      sourceBranchId,
      targetBranchId,
      sourceUsesGroupEnd,
      sourceBaseExit: sourceUsesGroupEnd
        ? primaryEnd(sourceGroup.bounds, options.direction)
        : pointPrimary(edge.from, options.direction),
      targetBaseEntry: targetUsesGroupStart
        ? primaryStart(targetGroup.bounds, options.direction)
        : pointPrimary(edge.to, options.direction),
    };
    routeInfoByEdge.set(index, routeInfo);
    constraints.push(routeInfo);
  });

  const solution = solveAssetGroupConstraints({
    direction: options.direction,
    ranksep: options.ranksep,
    trailingGroupPadding: options.trailingGroupPadding,
    groups: layout.groups,
    parentById: options.groupParentById,
    constraints,
  });

  const groups: RoutingLayout['groups'] = {};
  for (const [id, group] of Object.entries(layout.groups)) {
    const shift = solution.shiftByGroupId[id];
    const end = solution.endByGroupId[id];
    if (shift === undefined || end === undefined) {
      throw new Error('Missing solved asset group geometry');
    }
    groups[id] = {
      ...group,
      bounds: withForwardEnd(
        translateBounds(group.bounds, shift, options.direction),
        end,
        options.direction,
      ),
    };
  }

  const nodes: RoutingLayout['nodes'] = {};
  for (const [id, node] of Object.entries(layout.nodes)) {
    const ownerGroupId = options.ownerGroupByNodeId[id];
    const shift =
      ownerGroupId === null || ownerGroupId === undefined
        ? 0
        : solution.shiftByGroupId[ownerGroupId];
    if (shift === undefined) {
      throw new Error('Missing node owner asset group');
    }
    nodes[id] = {...node, bounds: translateBounds(node.bounds, shift, options.direction)};
  }

  const edges = layout.edges.map((edge, index) => {
    const sourceEndpointGroupId = options.endpointGroupById[edge.fromId];
    const targetEndpointGroupId = options.endpointGroupById[edge.toId];
    const sourceShift = sourceEndpointGroupId ? solution.shiftByGroupId[sourceEndpointGroupId] : 0;
    const targetShift = targetEndpointGroupId ? solution.shiftByGroupId[targetEndpointGroupId] : 0;
    if (sourceShift === undefined || targetShift === undefined) {
      throw new Error('Missing edge endpoint asset group');
    }
    const {sourceBoundary: _sourceBoundary, targetBoundary: _targetBoundary, ...legacyEdge} = edge;
    const translated = {
      ...legacyEdge,
      from: translatePoint(edge.from, sourceShift, options.direction),
      to: translatePoint(edge.to, targetShift, options.direction),
    };
    const routeInfo = routeInfoByEdge.get(index);
    if (
      !routeInfo ||
      solution.componentByGroupId[routeInfo.sourceBranchId] ===
        solution.componentByGroupId[routeInfo.targetBranchId]
    ) {
      return translated;
    }
    const sourceBranchShift = solution.shiftByGroupId[routeInfo.sourceBranchId]!;
    const targetBranchShift = solution.shiftByGroupId[routeInfo.targetBranchId]!;
    return {
      ...translated,
      sourceBoundary: routeInfo.sourceUsesGroupEnd
        ? solution.endByGroupId[routeInfo.sourceBranchId]!
        : routeInfo.sourceBaseExit + sourceBranchShift,
      targetBoundary: routeInfo.targetBaseEntry + targetBranchShift,
    };
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
    const result = applyAssetGroupLineageRoutingImpl(layout, options);
    return validateRoutingResult(layout, result, options) ? result : layout;
  } catch {
    return layout;
  }
};
