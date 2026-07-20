export type GroupParentById = Record<string, string | null>;

export type GroupAncestryIndex = {
  lowestCommonAncestor: (a: string, b: string) => string | null;
  branchBelow: (groupId: string, ancestorId: string | null) => string | null;
};

export const buildGroupAncestryIndex = (
  parentById: GroupParentById,
): GroupAncestryIndex => {
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
