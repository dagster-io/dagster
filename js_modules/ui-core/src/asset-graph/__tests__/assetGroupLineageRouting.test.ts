import type {IBounds} from '../../graph/common';

import {buildGroupAncestryIndex, solveAssetGroupConstraints} from '../assetGroupLineageRouting';

const bounds = (x: number, y: number, width: number, height: number): IBounds => ({
  x,
  y,
  width,
  height,
});

describe('buildGroupAncestryIndex', () => {
  it('finds common ancestors and branches below ancestors', () => {
    const index = buildGroupAncestryIndex({
      source: null,
      'source/inner': 'source',
      'source/inner/leaf': 'source/inner',
      target: null,
      'target/leaf': 'target',
    });

    expect(index.lowestCommonAncestor('source/inner', 'source/inner/leaf')).toBe('source/inner');
    expect(index.lowestCommonAncestor('source/inner/leaf', 'target/leaf')).toBe(null);
    expect(index.branchBelow('source/inner/leaf', 'source')).toBe('source/inner');
    expect(index.branchBelow('target/leaf', null)).toBe('target');
  });

  it('rejects cycles in the visible asset group parent hierarchy', () => {
    expect(() => buildGroupAncestryIndex({a: 'b', b: 'a'})).toThrow('Asset group parent cycle');
  });

  it('finds sibling and cousin common ancestors', () => {
    const index = buildGroupAncestryIndex({
      root: null,
      left: 'root',
      'left/one': 'left',
      'left/two': 'left',
      right: 'root',
      'right/one': 'right',
    });

    expect(index.lowestCommonAncestor('left/one', 'left/two')).toBe('left');
    expect(index.lowestCommonAncestor('left/one', 'right/one')).toBe('root');
  });

  it('handles roots, identical groups, and non-ancestor branches', () => {
    const index = buildGroupAncestryIndex({
      root: null,
      left: 'root',
      'left/leaf': 'left',
      right: 'root',
    });

    expect(index.lowestCommonAncestor('root', 'root')).toBe('root');
    expect(index.lowestCommonAncestor('left/leaf', 'left/leaf')).toBe('left/leaf');
    expect(index.branchBelow('root', 'root')).toBe(null);
    expect(index.branchBelow('left/leaf', 'right')).toBe(null);
  });

  it('rejects missing parents and unknown lookup groups', () => {
    expect(() => buildGroupAncestryIndex({child: 'missing'})).toThrow(
      'Missing visible asset group parent: missing',
    );

    const index = buildGroupAncestryIndex({root: null});
    expect(() => index.lowestCommonAncestor('root', 'missing')).toThrow(
      'Unknown visible asset group: missing',
    );
    expect(() => index.branchBelow('root', 'missing')).toThrow(
      'Unknown visible asset group: missing',
    );
  });

  it('indexes deep hierarchies without recursive stack growth', () => {
    const parentById: Record<string, string | null> = {};
    const groupId = (index: number) => `group-${index.toString().padStart(5, '0')}`;
    const groupCount = 20_000;
    for (let index = 0; index < groupCount; index++) {
      parentById[groupId(index)] = index === 0 ? null : groupId(index - 1);
    }

    const index = buildGroupAncestryIndex(parentById);
    expect(index.lowestCommonAncestor(groupId(groupCount - 1), groupId(10_000))).toBe(
      groupId(10_000),
    );
    expect(index.branchBelow(groupId(groupCount - 1), groupId(0))).toBe(groupId(1));
  });
});

describe('solveAssetGroupConstraints', () => {
  it('uses maximum horizontal fan-in and propagates only the minimum shift', () => {
    const solution = solveAssetGroupConstraints({
      direction: 'horizontal',
      ranksep: 60,
      trailingGroupPadding: 15,
      groups: {
        a: {bounds: bounds(0, 0, 100, 100), expanded: false},
        b: {bounds: bounds(20, 150, 130, 100), expanded: false},
        c: {bounds: bounds(180, 0, 100, 100), expanded: false},
        d: {bounds: bounds(300, 0, 100, 100), expanded: false},
      },
      parentById: {a: null, b: null, c: null, d: null},
      constraints: [
        {
          sourceBranchId: 'a',
          targetBranchId: 'c',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 100,
          targetBaseEntry: 180,
        },
        {
          sourceBranchId: 'b',
          targetBranchId: 'c',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 150,
          targetBaseEntry: 180,
        },
        {
          sourceBranchId: 'c',
          targetBranchId: 'd',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 280,
          targetBaseEntry: 300,
        },
      ],
    });

    expect(solution.shiftByGroupId).toEqual({a: 0, b: 0, c: 30, d: 70});
  });

  it('extends a parent envelope when a nested child moves', () => {
    const solution = solveAssetGroupConstraints({
      direction: 'horizontal',
      ranksep: 60,
      trailingGroupPadding: 15,
      groups: {
        source: {bounds: bounds(0, 0, 100, 100), expanded: false},
        parent: {bounds: bounds(150, 0, 200, 200), expanded: true},
        child: {bounds: bounds(160, 40, 100, 100), expanded: false},
        downstream: {bounds: bounds(400, 0, 100, 100), expanded: false},
      },
      parentById: {source: null, parent: null, child: 'parent', downstream: null},
      constraints: [
        {
          sourceBranchId: 'source',
          targetBranchId: 'child',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 100,
          targetBaseEntry: 160,
        },
        {
          sourceBranchId: 'parent',
          targetBranchId: 'downstream',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 350,
          targetBaseEntry: 400,
        },
      ],
    });

    expect(solution.shiftByGroupId.child).toBe(0);
    expect(solution.endByGroupId.parent).toBe(350);
    expect(solution.shiftByGroupId.downstream).toBe(10);
  });

  it('collapses a pseudo-cycle and ignores its internal cyclic clearance', () => {
    const solution = solveAssetGroupConstraints({
      direction: 'vertical',
      ranksep: 20,
      trailingGroupPadding: 16,
      groups: {
        upstream: {bounds: bounds(0, 0, 100, 100), expanded: false},
        a: {bounds: bounds(0, 100, 100, 100), expanded: false},
        b: {bounds: bounds(150, 100, 100, 100), expanded: false},
      },
      parentById: {upstream: null, a: null, b: null},
      constraints: [
        {
          sourceBranchId: 'a',
          targetBranchId: 'b',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 200,
          targetBaseEntry: 100,
        },
        {
          sourceBranchId: 'b',
          targetBranchId: 'a',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 200,
          targetBaseEntry: 100,
        },
        {
          sourceBranchId: 'upstream',
          targetBranchId: 'a',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 100,
          targetBaseEntry: 100,
        },
      ],
    });

    expect(solution.shiftByGroupId.a).toBe(20);
    expect(solution.shiftByGroupId.b).toBe(20);
    expect(solution.componentByGroupId.a).toBe(solution.componentByGroupId.b);
  });
});
