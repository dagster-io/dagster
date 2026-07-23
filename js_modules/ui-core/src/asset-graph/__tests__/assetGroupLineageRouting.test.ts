import type {IBounds} from '../../graph/common';
import {
  type ApplyAssetGroupRoutingOptions,
  type RoutingLayout,
  applyAssetGroupLineageRouting,
  buildGroupAncestryIndex,
  solveAssetGroupConstraints,
} from '../assetGroupLineageRouting';

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
        source: {bounds: bounds(0, 0, 180, 100), expanded: false},
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
          sourceBaseExit: 180,
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

    // 180 + 60 - 160 moves only the child by 80. Its new end (340) plus 15 padding
    // extends the parent end to 355, which then pushes downstream by 355 + 60 - 400 = 15.
    expect(solution.shiftByGroupId.parent).toBe(0);
    expect(solution.shiftByGroupId.child).toBe(80);
    expect(solution.endByGroupId.parent).toBe(355);
    expect(solution.shiftByGroupId.downstream).toBe(15);
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

  it('moves a parent and child atomically when they share a lineage component', () => {
    const solution = solveAssetGroupConstraints({
      direction: 'vertical',
      ranksep: 20,
      trailingGroupPadding: 16,
      groups: {
        upstream: {bounds: bounds(0, 0, 100, 100), expanded: false},
        parent: {bounds: bounds(0, 100, 100, 100), expanded: true},
        child: {bounds: bounds(0, 120, 100, 100), expanded: false},
      },
      parentById: {upstream: null, parent: null, child: 'parent'},
      constraints: [
        {
          sourceBranchId: 'parent',
          targetBranchId: 'child',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 200,
          targetBaseEntry: 120,
        },
        {
          sourceBranchId: 'child',
          targetBranchId: 'parent',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 220,
          targetBaseEntry: 100,
        },
        {
          sourceBranchId: 'upstream',
          targetBranchId: 'parent',
          sourceUsesGroupEnd: true,
          sourceBaseExit: 100,
          targetBaseEntry: 100,
        },
      ],
    });

    expect(solution.shiftByGroupId.parent).toBe(20);
    expect(solution.shiftByGroupId.child).toBe(20);
    expect(solution.componentByGroupId.parent).toBe(solution.componentByGroupId.child);
    expect(solution.endByGroupId.parent).toBe(256);
  });

  it('preserves the least solution when parallel constraints are duplicated', () => {
    const input = {
      direction: 'horizontal' as const,
      ranksep: 60,
      trailingGroupPadding: 15,
      groups: {
        source: {bounds: bounds(0, 0, 100, 100), expanded: false},
        target: {bounds: bounds(200, 0, 100, 100), expanded: false},
      },
      parentById: {source: null, target: null},
      constraints: [
        {
          sourceBranchId: 'source',
          targetBranchId: 'target',
          sourceUsesGroupEnd: false,
          sourceBaseExit: 100,
          targetBaseEntry: 200,
        },
        {
          sourceBranchId: 'source',
          targetBranchId: 'target',
          sourceUsesGroupEnd: false,
          sourceBaseExit: 170,
          targetBaseEntry: 200,
        },
      ],
    };
    const withoutDuplicates = solveAssetGroupConstraints(input);
    const withDuplicates = solveAssetGroupConstraints({
      ...input,
      constraints: [...input.constraints, input.constraints[0]!, input.constraints[1]!],
    });

    expect(withDuplicates.shiftByGroupId).toEqual(withoutDuplicates.shiftByGroupId);
    expect(withDuplicates.shiftByGroupId.target).toBe(30);
  });
});

const routingOptions = (
  overrides: Partial<ApplyAssetGroupRoutingOptions> = {},
): ApplyAssetGroupRoutingOptions => ({
  direction: 'horizontal',
  ranksep: 60,
  trailingGroupPadding: 15,
  margin: 100,
  groupParentById: {source: null, target: null},
  ownerGroupByNodeId: {sourceNode: 'source', targetNode: 'target'},
  endpointGroupById: {sourceNode: 'source', targetNode: 'target'},
  ...overrides,
});

describe('applyAssetGroupLineageRouting', () => {
  it('moves an LR target branch and adds scalar boundary corridors', () => {
    const layout: RoutingLayout = {
      width: 400,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(220, 120, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(200, 100, 120, 100), expanded: true},
      },
      edges: [
        {from: {x: 100, y: 40}, fromId: 'sourceNode', to: {x: 220, y: 140}, toId: 'targetNode'},
      ],
    };

    const result = applyAssetGroupLineageRouting(layout, routingOptions());

    expect(result).not.toBe(layout);
    expect(result.groups.source!.bounds).toEqual(bounds(0, 0, 180, 100));
    expect(result.groups.target!.bounds).toEqual(bounds(240, 100, 120, 100));
    expect(result.nodes.sourceNode!.bounds).toEqual(bounds(20, 20, 80, 40));
    expect(result.nodes.targetNode!.bounds).toEqual(bounds(260, 120, 80, 40));
    expect(result.edges[0]).toEqual({
      from: {x: 100, y: 40},
      fromId: 'sourceNode',
      to: {x: 260, y: 140},
      toId: 'targetNode',
      sourceBoundary: 180,
      targetBoundary: 240,
    });
  });

  it('falls back atomically when routing would partially translate a grouped-to-ungrouped edge', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(220, 120, 80, 40)},
        ungroupedNode: {id: 'ungroupedNode', bounds: bounds(400, 120, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(200, 100, 120, 100), expanded: true},
      },
      edges: [
        {from: {x: 100, y: 40}, fromId: 'sourceNode', to: {x: 220, y: 140}, toId: 'targetNode'},
        {
          from: {x: 300, y: 140},
          fromId: 'targetNode',
          to: {x: 400, y: 140},
          toId: 'ungroupedNode',
        },
      ],
    };

    expect(
      applyAssetGroupLineageRouting(
        layout,
        routingOptions({
          ownerGroupByNodeId: {
            sourceNode: 'source',
            targetNode: 'target',
            ungroupedNode: null,
          },
          endpointGroupById: {
            sourceNode: 'source',
            targetNode: 'target',
            ungroupedNode: null,
          },
        }),
      ),
    ).toBe(layout);
  });

  it('allows a grouped-to-ungrouped edge when both endpoint translations are zero', () => {
    const layout: RoutingLayout = {
      width: 600,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 120, 80, 40)},
        ungroupedNode: {id: 'ungroupedNode', bounds: bounds(500, 120, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 100, 120, 100), expanded: true},
      },
      edges: [
        {from: {x: 100, y: 40}, fromId: 'sourceNode', to: {x: 320, y: 140}, toId: 'targetNode'},
        {
          from: {x: 400, y: 140},
          fromId: 'targetNode',
          to: {x: 500, y: 140},
          toId: 'ungroupedNode',
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        ownerGroupByNodeId: {
          sourceNode: 'source',
          targetNode: 'target',
          ungroupedNode: null,
        },
        endpointGroupById: {
          sourceNode: 'source',
          targetNode: 'target',
          ungroupedNode: null,
        },
      }),
    );

    expect(result).not.toBe(layout);
    expect(result.edges[1]).toEqual(layout.edges[1]);
  });

  it('returns the exact input object for invalid options', () => {
    const layout: RoutingLayout = {
      width: 100,
      height: 100,
      nodes: {},
      groups: {},
      edges: [],
    };

    expect(applyAssetGroupLineageRouting(layout, routingOptions({ranksep: Number.NaN}))).toBe(
      layout,
    );
    expect(applyAssetGroupLineageRouting(layout, routingOptions({trailingGroupPadding: -1}))).toBe(
      layout,
    );
  });

  it('returns the exact input object when routed canvas arithmetic overflows', () => {
    const layout: RoutingLayout = {
      width: 100,
      height: 100,
      nodes: {},
      groups: {
        source: {
          id: 'source',
          bounds: bounds(Number.MAX_VALUE, 0, 0, 10),
          expanded: true,
        },
      },
      edges: [],
    };

    expect(
      applyAssetGroupLineageRouting(
        layout,
        routingOptions({
          margin: Number.MAX_VALUE,
          groupParentById: {source: null},
          ownerGroupByNodeId: {},
          endpointGroupById: {},
        }),
      ),
    ).toBe(layout);
  });

  it('supports TB routing without changing perpendicular node coordinates', () => {
    const layout: RoutingLayout = {
      width: 300,
      height: 500,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 40, 80)},
        targetNode: {id: 'targetNode', bounds: bounds(120, 220, 40, 80)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 100, 180), expanded: true},
        target: {id: 'target', bounds: bounds(100, 200, 100, 120), expanded: true},
      },
      edges: [
        {from: {x: 40, y: 100}, fromId: 'sourceNode', to: {x: 140, y: 220}, toId: 'targetNode'},
      ],
    };

    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({direction: 'vertical', ranksep: 20, trailingGroupPadding: 16}),
    );

    expect(result.groups.source!.bounds).toEqual(bounds(0, 0, 100, 180));
    expect(result.groups.target!.bounds).toEqual(bounds(100, 200, 100, 120));
    expect(result.nodes.sourceNode!.bounds.x).toBe(20);
    expect(result.nodes.targetNode!.bounds.x).toBe(120);
    expect(result.edges[0]).toEqual({
      from: {x: 40, y: 100},
      fromId: 'sourceNode',
      to: {x: 140, y: 220},
      toId: 'targetNode',
      sourceBoundary: 180,
      targetBoundary: 200,
    });
  });

  it('routes LR from an ancestor endpoint into only the crossed child boundary', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        ancestorNode: {id: 'ancestorNode', bounds: bounds(20, 20, 80, 40)},
        descendantNode: {id: 'descendantNode', bounds: bounds(140, 60, 40, 40)},
      },
      groups: {
        a: {id: 'a', bounds: bounds(0, 0, 300, 200), expanded: true},
        'a/b': {id: 'a/b', bounds: bounds(120, 40, 100, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'ancestorNode',
          to: {x: 140, y: 80},
          toId: 'descendantNode',
        },
      ],
    };
    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        groupParentById: {a: null, 'a/b': 'a'},
        ownerGroupByNodeId: {ancestorNode: 'a', descendantNode: 'a/b'},
        endpointGroupById: {ancestorNode: 'a', descendantNode: 'a/b'},
      }),
    );

    expect(result.groups['a/b']!.bounds).toEqual(bounds(160, 40, 100, 100));
    expect(result.nodes.descendantNode!.bounds.y).toBe(60);
    expect(result.edges[0]).toMatchObject({
      from: {x: 100, y: 40},
      to: {x: 180, y: 80},
      sourceBoundary: 100,
      targetBoundary: 160,
    });
    expect(result.edges[0]!.sourceBoundary).not.toBe(300);
  });

  it('routes TB from an ancestor endpoint into only the crossed child boundary', () => {
    const layout: RoutingLayout = {
      width: 300,
      height: 500,
      nodes: {
        ancestorNode: {id: 'ancestorNode', bounds: bounds(20, 20, 40, 80)},
        descendantNode: {id: 'descendantNode', bounds: bounds(60, 130, 40, 40)},
      },
      groups: {
        a: {id: 'a', bounds: bounds(0, 0, 200, 300), expanded: true},
        'a/b': {id: 'a/b', bounds: bounds(40, 110, 100, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 40, y: 100},
          fromId: 'ancestorNode',
          to: {x: 80, y: 130},
          toId: 'descendantNode',
        },
      ],
    };
    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        direction: 'vertical',
        ranksep: 20,
        trailingGroupPadding: 16,
        groupParentById: {a: null, 'a/b': 'a'},
        ownerGroupByNodeId: {ancestorNode: 'a', descendantNode: 'a/b'},
        endpointGroupById: {ancestorNode: 'a', descendantNode: 'a/b'},
      }),
    );

    expect(result.groups['a/b']!.bounds).toEqual(bounds(40, 120, 100, 100));
    expect(result.nodes.descendantNode!.bounds.x).toBe(60);
    expect(result.edges[0]).toMatchObject({
      from: {x: 40, y: 100},
      to: {x: 80, y: 140},
      sourceBoundary: 100,
      targetBoundary: 120,
    });
    expect(result.edges[0]!.sourceBoundary).not.toBe(300);
  });

  it('keeps edges within the same exact endpoint group on the legacy path', () => {
    const layout: RoutingLayout = {
      width: 300,
      height: 200,
      nodes: {
        first: {id: 'first', bounds: bounds(20, 20, 40, 40)},
        second: {id: 'second', bounds: bounds(160, 20, 40, 40)},
      },
      groups: {a: {id: 'a', bounds: bounds(0, 0, 240, 100), expanded: true}},
      edges: [{from: {x: 60, y: 40}, fromId: 'first', to: {x: 160, y: 40}, toId: 'second'}],
    };
    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        groupParentById: {a: null},
        ownerGroupByNodeId: {first: 'a', second: 'a'},
        endpointGroupById: {first: 'a', second: 'a'},
      }),
    );

    expect(result.edges[0]).toEqual(layout.edges[0]);
    expect(result.edges[0]!.sourceBoundary).toBeUndefined();
    expect(result.edges[0]!.targetBoundary).toBeUndefined();
  });

  it('routes descendant exit to an ancestor endpoint only when baseline clearance is sufficient', () => {
    const sufficient: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        descendantNode: {id: 'descendantNode', bounds: bounds(40, 40, 60, 40)},
        ancestorNode: {id: 'ancestorNode', bounds: bounds(220, 120, 40, 40)},
      },
      groups: {
        a: {id: 'a', bounds: bounds(0, 0, 300, 200), expanded: true},
        'a/b': {id: 'a/b', bounds: bounds(20, 20, 100, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 60},
          fromId: 'descendantNode',
          to: {x: 220, y: 140},
          toId: 'ancestorNode',
        },
      ],
    };
    const options = routingOptions({
      groupParentById: {a: null, 'a/b': 'a'},
      ownerGroupByNodeId: {ancestorNode: 'a', descendantNode: 'a/b'},
      endpointGroupById: {ancestorNode: 'a', descendantNode: 'a/b'},
    });

    const result = applyAssetGroupLineageRouting(sufficient, options);
    expect(result.edges[0]).toMatchObject({sourceBoundary: 120, targetBoundary: 220});
    expect(result.edges[0]!.targetBoundary).not.toBe(0);

    const insufficient: RoutingLayout = {
      ...sufficient,
      nodes: {
        ...sufficient.nodes,
        ancestorNode: {id: 'ancestorNode', bounds: bounds(150, 120, 40, 40)},
      },
      edges: [
        {
          from: {x: 100, y: 60},
          fromId: 'descendantNode',
          to: {x: 150, y: 140},
          toId: 'ancestorNode',
        },
      ],
    };
    expect(applyAssetGroupLineageRouting(insufficient, options)).toBe(insufficient);
  });

  it('terminates opposite ancestor-descendant routing with atomic fallback', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        ancestorNode: {id: 'ancestorNode', bounds: bounds(20, 20, 80, 40)},
        descendantNode: {id: 'descendantNode', bounds: bounds(140, 60, 40, 40)},
      },
      groups: {
        a: {id: 'a', bounds: bounds(0, 0, 300, 200), expanded: true},
        'a/b': {id: 'a/b', bounds: bounds(120, 40, 100, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'ancestorNode',
          to: {x: 140, y: 80},
          toId: 'descendantNode',
        },
        {
          from: {x: 180, y: 80},
          fromId: 'descendantNode',
          to: {x: 100, y: 40},
          toId: 'ancestorNode',
        },
      ],
    };

    expect(
      applyAssetGroupLineageRouting(
        layout,
        routingOptions({
          groupParentById: {a: null, 'a/b': 'a'},
          ownerGroupByNodeId: {ancestorNode: 'a', descendantNode: 'a/b'},
          endpointGroupById: {ancestorNode: 'a', descendantNode: 'a/b'},
        }),
      ),
    ).toBe(layout);
    expect(layout.groups['a/b']!.bounds.x).toBe(120);
  });

  it('uses outer divergent branches and leaves unrelated rectangles untouched', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 500,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(30, 30, 60, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(230, 130, 60, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 200), expanded: true},
        sourceLeaf: {id: 'sourceLeaf', bounds: bounds(20, 20, 120, 100), expanded: true},
        target: {id: 'target', bounds: bounds(200, 100, 140, 160), expanded: true},
        targetLeaf: {id: 'targetLeaf', bounds: bounds(220, 120, 100, 100), expanded: true},
        unrelated: {id: 'unrelated', bounds: bounds(185, 280, 100, 100), expanded: true},
      },
      edges: [
        {from: {x: 90, y: 50}, fromId: 'sourceNode', to: {x: 230, y: 150}, toId: 'targetNode'},
      ],
    };
    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        groupParentById: {
          source: null,
          sourceLeaf: 'source',
          target: null,
          targetLeaf: 'target',
          unrelated: null,
        },
        ownerGroupByNodeId: {sourceNode: 'sourceLeaf', targetNode: 'targetLeaf'},
        endpointGroupById: {sourceNode: 'sourceLeaf', targetNode: 'targetLeaf'},
      }),
    );

    expect(result.groups.target!.bounds.x).toBe(240);
    expect(result.groups.unrelated).toEqual(layout.groups.unrelated);
    expect(result.edges[0]).toEqual({
      from: {x: 90, y: 50},
      fromId: 'sourceNode',
      to: {x: 270, y: 150},
      toId: 'targetNode',
      sourceBoundary: 180,
      targetBoundary: 240,
    });
    expect(Object.keys(result.edges[0]!).sort()).toEqual(
      ['from', 'fromId', 'sourceBoundary', 'targetBoundary', 'to', 'toId'].sort(),
    );
  });

  it('keeps pseudo-cycle geometry and omits corridors for SCC-internal edges', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        aNode: {id: 'aNode', bounds: bounds(20, 20, 40, 40)},
        bNode: {id: 'bNode', bounds: bounds(220, 20, 40, 40)},
      },
      groups: {
        a: {id: 'a', bounds: bounds(0, 0, 100, 100), expanded: true},
        b: {id: 'b', bounds: bounds(200, 0, 100, 100), expanded: true},
      },
      edges: [
        {from: {x: 60, y: 40}, fromId: 'aNode', to: {x: 220, y: 40}, toId: 'bNode'},
        {from: {x: 260, y: 60}, fromId: 'bNode', to: {x: 20, y: 60}, toId: 'aNode'},
      ],
    };
    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        groupParentById: {a: null, b: null},
        ownerGroupByNodeId: {aNode: 'a', bNode: 'b'},
        endpointGroupById: {aNode: 'a', bNode: 'b'},
      }),
    );

    expect(result.groups.b!.bounds.x - result.groups.a!.bounds.x).toBe(200);
    expect(result.edges).toEqual(layout.edges);
    expect(result.edges.every((edge) => edge.sourceBoundary === undefined)).toBe(true);
  });

  it('is stateless across calls and returns worker-serializable output', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 120, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 100, 120, 100), expanded: true},
      },
      edges: [
        {from: {x: 100, y: 40}, fromId: 'sourceNode', to: {x: 320, y: 140}, toId: 'targetNode'},
      ],
    };
    const originalSnapshot = JSON.parse(JSON.stringify(layout));

    const result = applyAssetGroupLineageRouting(layout, routingOptions());
    const repeated = applyAssetGroupLineageRouting(result, routingOptions());

    expect(result.groups.target!.bounds.x).toBe(300);
    expect(repeated.groups.target!.bounds).toEqual(result.groups.target!.bounds);
    expect(repeated.nodes.targetNode!.bounds).toEqual(result.nodes.targetNode!.bounds);
    expect(repeated.edges).toEqual(result.edges);
    expect(layout).toEqual(originalSnapshot);
    expect(JSON.parse(JSON.stringify(result))).toEqual(result);
  });

  it('routes layouts larger than the engine argument limit without atomic fallback', () => {
    const nodes: RoutingLayout['nodes'] = {
      sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
      targetNode: {id: 'targetNode', bounds: bounds(220, 120, 80, 40)},
    };
    for (let index = 0; index < 150_000; index++) {
      const id = `filler-${index}`;
      nodes[id] = {id, bounds: bounds(0, 250, 1, 1)};
    }
    const layout: RoutingLayout = {
      width: 400,
      height: 300,
      nodes,
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(200, 100, 120, 100), expanded: true},
      },
      edges: [
        {from: {x: 100, y: 40}, fromId: 'sourceNode', to: {x: 220, y: 140}, toId: 'targetNode'},
      ],
    };

    const result = applyAssetGroupLineageRouting(layout, routingOptions());

    expect(result.groups.target!.bounds.x).toBe(240);
    expect(result.edges[0]!.targetBoundary).toBe(240);
  }, 30_000);

  it('covers every nested boundary with the outer three-level divergent branches', () => {
    const layout: RoutingLayout = {
      width: 600,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(40, 40, 40, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(240, 40, 40, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 180), expanded: true},
        sourceMid: {id: 'sourceMid', bounds: bounds(20, 20, 130, 130), expanded: true},
        sourceLeaf: {id: 'sourceLeaf', bounds: bounds(30, 30, 80, 80), expanded: true},
        target: {id: 'target', bounds: bounds(200, 0, 150, 180), expanded: true},
        targetMid: {id: 'targetMid', bounds: bounds(220, 20, 110, 130), expanded: true},
        targetLeaf: {id: 'targetLeaf', bounds: bounds(230, 30, 80, 80), expanded: true},
      },
      edges: [
        {from: {x: 80, y: 60}, fromId: 'sourceNode', to: {x: 240, y: 60}, toId: 'targetNode'},
      ],
    };
    const result = applyAssetGroupLineageRouting(
      layout,
      routingOptions({
        groupParentById: {
          source: null,
          sourceMid: 'source',
          sourceLeaf: 'sourceMid',
          target: null,
          targetMid: 'target',
          targetLeaf: 'targetMid',
        },
        ownerGroupByNodeId: {sourceNode: 'sourceLeaf', targetNode: 'targetLeaf'},
        endpointGroupById: {sourceNode: 'sourceLeaf', targetNode: 'targetLeaf'},
      }),
    );

    expect(result.edges[0]!.sourceBoundary).toBe(180);
    expect(result.edges[0]!.targetBoundary).toBe(240);
    expect(result.groups.target!.bounds.x).toBe(240);
    expect(result.groups.targetMid!.bounds.x).toBe(260);
    expect(result.groups.targetLeaf!.bounds.x).toBe(270);
  });

  it('falls back atomically when the layout is invalid', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, -1, 40)}},
      groups: {source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true}},
      edges: [],
    };
    expect(
      applyAssetGroupLineageRouting(
        layout,
        routingOptions({
          groupParentById: {source: null},
          ownerGroupByNodeId: {sourceNode: 'source'},
          endpointGroupById: {sourceNode: 'source'},
        }),
      ),
    ).toBe(layout);
  });

  it('falls back rather than partially repairing one-sided corridor metadata', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 120, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 100, 120, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'sourceNode',
          to: {x: 320, y: 140},
          toId: 'targetNode',
          sourceBoundary: 180,
        },
      ],
    };

    expect(applyAssetGroupLineageRouting(layout, routingOptions())).toBe(layout);
  });

  it('falls back for paired input corridors that violate primary-axis separation', () => {
    const layout: RoutingLayout = {
      width: 500,
      height: 300,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 120, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 100, 120, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'sourceNode',
          to: {x: 320, y: 140},
          toId: 'targetNode',
          sourceBoundary: 180,
          targetBoundary: 230,
        },
      ],
    };

    expect(applyAssetGroupLineageRouting(layout, routingOptions())).toBe(layout);
  });
});

describe('applyAssetGroupLineageRouting secondary-axis alignment', () => {
  const alignedOptions = (
    overrides: Partial<ApplyAssetGroupRoutingOptions> = {},
  ): ApplyAssetGroupRoutingOptions =>
    routingOptions({alignGroupsOnSecondaryAxis: true, ...overrides});

  it('leaves the secondary axis untouched when alignment is not requested', () => {
    const layout: RoutingLayout = {
      width: 600,
      height: 700,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 420, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 400, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'sourceNode',
          to: {x: 320, y: 440},
          toId: 'targetNode',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(layout, routingOptions());

    expect(result.groups.target!.bounds).toEqual(bounds(300, 400, 180, 100));
    expect(result.nodes.targetNode!.bounds).toEqual(bounds(320, 420, 80, 40));
    expect(result.edges[0]!.to).toEqual({x: 320, y: 440});
  });

  it('slides a downstream group onto the secondary axis position of its upstream endpoint', () => {
    const layout: RoutingLayout = {
      width: 600,
      height: 700,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 420, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 400, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'sourceNode',
          to: {x: 320, y: 440},
          toId: 'targetNode',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(layout, alignedOptions());

    expect(result.groups.source!.bounds).toEqual(bounds(0, 0, 180, 100));
    expect(result.groups.target!.bounds).toEqual(bounds(300, 0, 180, 100));
    expect(result.nodes.targetNode!.bounds).toEqual(bounds(320, 20, 80, 40));
    expect(result.edges[0]!.from).toEqual({x: 100, y: 40});
    expect(result.edges[0]!.to).toEqual({x: 320, y: 40});
  });

  it('preserves the primary-axis corridor while aligning the secondary axis', () => {
    const layout: RoutingLayout = {
      width: 600,
      height: 700,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 420, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 400, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'sourceNode',
          to: {x: 320, y: 440},
          toId: 'targetNode',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(layout, alignedOptions());
    const edge = result.edges[0]!;

    expect(edge.sourceBoundary).toBe(180);
    expect(edge.targetBoundary).toBe(300);
    expect(edge.from.x).toBeLessThanOrEqual(edge.sourceBoundary!);
    expect(edge.sourceBoundary! + 60).toBeLessThanOrEqual(edge.targetBoundary!);
    expect(edge.targetBoundary!).toBeLessThanOrEqual(edge.to.x);
  });

  it('cascades same-column groups apart instead of overlapping them', () => {
    const layout: RoutingLayout = {
      width: 700,
      height: 900,
      nodes: {
        a: {id: 'a', bounds: bounds(20, 20, 80, 40)},
        b: {id: 'b', bounds: bounds(20, 80, 80, 40)},
        t1n: {id: 't1n', bounds: bounds(320, 420, 80, 40)},
        t2n: {id: 't2n', bounds: bounds(320, 620, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 300), expanded: true},
        t1: {id: 't1', bounds: bounds(300, 400, 180, 100), expanded: true},
        t2: {id: 't2', bounds: bounds(300, 600, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'a',
          to: {x: 320, y: 440},
          toId: 't1n',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
        {
          from: {x: 100, y: 100},
          fromId: 'b',
          to: {x: 320, y: 640},
          toId: 't2n',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(
      layout,
      alignedOptions({
        groupParentById: {source: null, t1: null, t2: null},
        ownerGroupByNodeId: {a: 'source', b: 'source', t1n: 't1', t2n: 't2'},
        endpointGroupById: {a: 'source', b: 'source', t1n: 't1', t2n: 't2'},
      }),
    );

    // t2 wants y 60, which overlaps t1, so it cascades below t1's original 100px gap.
    expect(result.groups.t1!.bounds).toEqual(bounds(300, 0, 180, 100));
    expect(result.groups.t2!.bounds).toEqual(bounds(300, 200, 180, 100));
    expect(result.nodes.t2n!.bounds).toEqual(bounds(320, 220, 80, 40));
    expect(result.edges[1]!.to).toEqual({x: 320, y: 240});
  });

  it('preserves the upstream group order when cascading', () => {
    const layout: RoutingLayout = {
      width: 700,
      height: 900,
      nodes: {
        a: {id: 'a', bounds: bounds(20, 20, 80, 40)},
        b: {id: 'b', bounds: bounds(20, 80, 80, 40)},
        t1n: {id: 't1n', bounds: bounds(320, 420, 80, 40)},
        t2n: {id: 't2n', bounds: bounds(320, 620, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 300), expanded: true},
        t1: {id: 't1', bounds: bounds(300, 400, 180, 100), expanded: true},
        t2: {id: 't2', bounds: bounds(300, 600, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 100},
          fromId: 'b',
          to: {x: 320, y: 440},
          toId: 't1n',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
        {
          from: {x: 100, y: 40},
          fromId: 'a',
          to: {x: 320, y: 640},
          toId: 't2n',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(
      layout,
      alignedOptions({
        groupParentById: {source: null, t1: null, t2: null},
        ownerGroupByNodeId: {a: 'source', b: 'source', t1n: 't1', t2n: 't2'},
        endpointGroupById: {a: 'source', b: 'source', t1n: 't1', t2n: 't2'},
      }),
    );

    expect(result.groups.t1!.bounds.y).toBeLessThan(result.groups.t2!.bounds.y);
    expect(result.groups.t1!.bounds.y + result.groups.t1!.bounds.height).toBeLessThanOrEqual(
      result.groups.t2!.bounds.y,
    );
  });

  it('skips alignment when an edge endpoint has no owning group', () => {
    const layout: RoutingLayout = {
      width: 700,
      height: 900,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 20, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 420, 80, 40)},
        ungroupedNode: {id: 'ungroupedNode', bounds: bounds(560, 420, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 0, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 400, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 40},
          fromId: 'sourceNode',
          to: {x: 320, y: 440},
          toId: 'targetNode',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
        {from: {x: 480, y: 440}, fromId: 'targetNode', to: {x: 560, y: 440}, toId: 'ungroupedNode'},
      ],
    };

    const result = applyAssetGroupLineageRouting(
      layout,
      alignedOptions({
        ownerGroupByNodeId: {
          sourceNode: 'source',
          targetNode: 'target',
          ungroupedNode: null,
        },
        endpointGroupById: {
          sourceNode: 'source',
          targetNode: 'target',
          ungroupedNode: null,
        },
      }),
    );

    expect(result.groups.target!.bounds).toEqual(bounds(300, 400, 180, 100));
    expect(result.nodes.targetNode!.bounds).toEqual(bounds(320, 420, 80, 40));
  });

  it('grows the canvas when alignment pushes a group past the original extent', () => {
    const layout: RoutingLayout = {
      width: 600,
      height: 260,
      nodes: {
        sourceNode: {id: 'sourceNode', bounds: bounds(20, 120, 80, 40)},
        targetNode: {id: 'targetNode', bounds: bounds(320, 20, 80, 40)},
      },
      groups: {
        source: {id: 'source', bounds: bounds(0, 100, 180, 100), expanded: true},
        target: {id: 'target', bounds: bounds(300, 0, 180, 100), expanded: true},
      },
      edges: [
        {
          from: {x: 100, y: 140},
          fromId: 'sourceNode',
          to: {x: 320, y: 40},
          toId: 'targetNode',
          sourceBoundary: 180,
          targetBoundary: 300,
        },
      ],
    };

    const result = applyAssetGroupLineageRouting(layout, alignedOptions());

    expect(result.groups.target!.bounds).toEqual(bounds(300, 100, 180, 100));
    expect(result.height).toBeGreaterThanOrEqual(300);
  });
});
