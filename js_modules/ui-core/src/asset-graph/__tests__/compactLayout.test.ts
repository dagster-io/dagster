import type {IBounds} from '../../graph/common';
import {buildAssetKey, buildAssetNode} from '../../graphql/builders';
import {GraphData, buildGraphData, groupIdForNode} from '../Utils';
import * as CompactLayout from '../compactLayout';
import {CompactLayoutOptions, compactLayout} from '../compactLayout';
import {AssetGraphLayout, AssetLayoutDirection, layoutAssetGraph} from '../layout';

const OPTS: CompactLayoutOptions = {
  maxGap: 0,
  nodeGap: 0,
  groupGap: 20,
  groupPadding: {x: 10, top: 50, bottom: 10},
};

const box = (x: number, y: number, height = 100): IBounds => ({x, y, width: 100, height});

const overlaps = (a: IBounds, b: IBounds) =>
  a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

// Asset boxes are drawn inset from their layout bounds, and production uses a negative nodesep.
const inset = (b: IBounds): IBounds => ({
  x: b.x,
  y: b.y + 6,
  width: b.width,
  height: b.height - 12,
});

const contains = (outer: IBounds, inner: IBounds) =>
  inner.x >= outer.x &&
  inner.y >= outer.y &&
  inner.x + inner.width <= outer.x + outer.width &&
  inner.y + inner.height <= outer.y + outer.height;

describe('compactLayout', () => {
  it('closes gaps wider than maxGap and leaves narrower gaps alone', () => {
    const boxes = {a: box(0, 0), b: box(0, 150), c: box(0, 750)};
    compactLayout(
      {boxes, groups: [], parentOf: () => undefined, edges: []},
      {...OPTS, maxGap: 100, relax: false},
    );
    expect([boxes.a.y, boxes.b.y, boxes.c.y]).toEqual([0, 150, 350]);
  });

  it('compacts along x when axis is x, without changing y', () => {
    const boxes = {
      a: {x: 0, y: 0, width: 100, height: 100},
      b: {x: 150, y: 0, width: 100, height: 100},
      c: {x: 750, y: 50, width: 100, height: 100},
      d: {x: 900, y: 300, width: 100, height: 100},
    };
    compactLayout(
      {boxes, groups: [], parentOf: () => undefined, edges: []},
      {...OPTS, axis: 'x', maxGap: 100, relax: false},
    );
    expect(Object.values(boxes).map((b) => [b.x, b.y])).toEqual([
      [0, 0],
      [150, 0],
      [350, 50],
      [100, 300],
    ]);
  });

  it('uses the group header padding across the axis when compacting along x', () => {
    // `below` sits under the group's children but inside its header and bottom padding.
    const boxes = {child: box(500, 100), below: box(0, 220)};
    compactLayout(
      {
        boxes,
        groups: ['g'],
        parentOf: (id) => (id === 'child' ? 'g' : undefined),
        edges: [],
      },
      {...OPTS, axis: 'x', maxGap: 0, relax: false},
    );
    // The group spans y 50..210 (50 top, 10 bottom), so `below` at 220 doesn't overlap it.
    expect(boxes.below.x).toEqual(0);
    expect(boxes.child.x).toEqual(OPTS.groupPadding.x);
  });

  it('packs boxes tightly when maxGap is 0, without changing x', () => {
    const boxes = {a: box(0, 0), b: box(0, 150), c: box(200, 900)};
    compactLayout(
      {boxes, groups: [], parentOf: () => undefined, edges: []},
      {...OPTS, maxGap: 0, relax: false},
    );
    expect(boxes.a).toEqual(box(0, 0));
    expect(boxes.b).toEqual(box(0, 100));
    expect(boxes.c).toEqual(box(200, 0));
  });

  it('packs overlapping columns of different widths without overlaps', () => {
    // `wide` spans both narrow columns, so each narrow box must clear it.
    const boxes = {
      left: box(0, 0),
      wide: {x: 50, y: 300, width: 250, height: 100},
      right: box(200, 700),
      left2: box(0, 1200),
    };
    compactLayout(
      {boxes, groups: [], parentOf: () => undefined, edges: []},
      {...OPTS, maxGap: 0, relax: false},
    );
    expect([boxes.left.y, boxes.wide.y, boxes.right.y, boxes.left2.y]).toEqual([0, 100, 200, 200]);
  });

  it('moves boxes without edges up, letting the boxes below them follow their edges', () => {
    // Gaps under maxGap survive packing. `lonely` has no edges, and `child` is held below it.
    // `anchor` sits directly under `parent`, so `parent` can't move down to meet `child`.
    const boxes = {
      top: box(0, 0),
      lonely: box(0, 200),
      child: box(0, 400),
      parent: box(200, 0),
      anchor: box(200, 100, 400),
    };
    compactLayout(
      {boxes, groups: [], parentOf: () => undefined, edges: [{v: 'parent', w: 'child'}]},
      {...OPTS, maxGap: 250},
    );
    expect(boxes.lonely.y).toEqual(100);
    expect(boxes.child.y).toEqual(200);
  });

  it('keeps a single child level with its parent after packing', () => {
    // The parent's other children are stacked in column 1. `only` is the single child of
    // child2 and starts far below it, in column 2.
    const boxes = {
      parent: box(0, 300),
      child1: box(200, 0),
      child2: box(200, 300),
      child3: box(200, 600),
      only: box(400, 1500),
    };
    compactLayout(
      {
        boxes,
        groups: [],
        parentOf: () => undefined,
        edges: [
          {v: 'parent', w: 'child1'},
          {v: 'parent', w: 'child2'},
          {v: 'parent', w: 'child3'},
          {v: 'child2', w: 'only'},
        ],
      },
      OPTS,
    );
    expect(boxes.only.y).toEqual(boxes.child2.y);
  });

  it('moves expanded groups as rigid boxes and keeps their children inside them', () => {
    const boxes = {
      g1a: box(0, 100),
      g1b: box(0, 250),
      loose: box(0, 900),
      g2a: box(0, 2000),
    };
    const parents: {[id: string]: string} = {g1a: 'g1', g1b: 'g1', g2a: 'g2'};
    compactLayout(
      {
        boxes,
        groups: ['g1', 'g2'],
        parentOf: (id) => parents[id],
        edges: [],
      },
      {...OPTS, relax: false},
    );
    const groupBox = (children: IBounds[]): IBounds => {
      const pad = OPTS.groupPadding;
      const y0 = Math.min(...children.map((c) => c.y));
      const y1 = Math.max(...children.map((c) => c.y + c.height));
      return {
        x: -pad.x,
        y: y0 - pad.top,
        width: 100 + pad.x * 2,
        height: y1 - y0 + pad.top + pad.bottom,
      };
    };
    const g1 = groupBox([boxes.g1a, boxes.g1b]);
    const g2 = groupBox([boxes.g2a]);
    expect(boxes.g1b.y - boxes.g1a.y).toEqual(100);
    expect(boxes.loose.y).toEqual(g1.y + g1.height + OPTS.groupGap);
    expect(g2.y).toEqual(boxes.loose.y + 100 + OPTS.groupGap);
    expect(overlaps(g1, boxes.loose)).toBe(false);
    expect(overlaps(g2, boxes.loose)).toBe(false);
  });
});

describe('layoutAssetGraph compaction', () => {
  // `a1` fans out to four assets in group b; two of those have a single child in group c.
  // `a2` links straight to group c, so dagre routes it through hidden points in group b's column.
  const assets: {name: string; group: string; deps: string[]}[] = [
    {name: 'a1', group: 'a', deps: []},
    {name: 'a2', group: 'a', deps: []},
    {name: 'b1', group: 'b', deps: ['a1']},
    {name: 'b2', group: 'b', deps: ['a1']},
    {name: 'b3', group: 'b', deps: ['a1']},
    {name: 'b4', group: 'b', deps: ['a1']},
    {name: 'c2', group: 'c', deps: ['b2']},
    {name: 'c4', group: 'c', deps: ['b4']},
    {name: 'c5', group: 'c', deps: ['a2', 'b1']},
    {name: 'd1', group: 'd', deps: ['c5', 'a1', 'a2']},
  ];

  const graphData = (): GraphData => {
    const data = buildGraphData(
      assets.map(({name, group, deps}) =>
        buildAssetNode({
          id: JSON.stringify([name]),
          assetKey: buildAssetKey({path: [name]}),
          groupName: group,
          dependencyKeys: deps.map((d) => buildAssetKey({path: [d]})),
          dependedByKeys: assets
            .filter((other) => other.deps.includes(name))
            .map((other) => buildAssetKey({path: [other.name]})),
        }),
      ),
    );
    data.expandedGroups = [...new Set(Object.values(data.nodes).map(groupIdForNode))];
    return data;
  };

  const layoutWith = (
    compactionMaxGap: number | undefined,
    direction: AssetLayoutDirection = 'horizontal',
  ) =>
    layoutAssetGraph(graphData(), {
      direction,
      flagAssetGraphGroupsPerCodeLocation: false,
      facets: [],
      overrides: {compactionMaxGap},
    });

  const expectValidLayout = (layout: AssetGraphLayout, direction: AssetLayoutDirection) => {
    const nodes = Object.values(layout.nodes);
    for (const [i, a] of nodes.entries()) {
      for (const b of nodes.slice(i + 1)) {
        expect(overlaps(inset(a.bounds), inset(b.bounds))).toBe(false);
      }
    }
    for (const edge of layout.edges) {
      if (direction === 'horizontal') {
        expect(edge.to.x).toBeGreaterThan(edge.from.x);
      } else {
        expect(edge.to.y).toBeGreaterThan(edge.from.y);
      }
    }
    const groups = Object.values(layout.groups);
    for (const node of Object.values(graphData().nodes)) {
      const group = layout.groups[groupIdForNode(node)];
      const bounds = layout.nodes[node.id]?.bounds;
      expect(group && bounds && contains(group.bounds, bounds)).toBe(true);
      for (const other of groups) {
        if (other !== group && bounds) {
          expect(overlaps(other.bounds, bounds)).toBe(false);
        }
      }
    }
  };

  it.each([
    ['horizontal', 0],
    ['horizontal', 250],
    ['horizontal', 500],
    ['vertical', 0],
    ['vertical', 250],
    ['vertical', 500],
  ] as const)('produces a valid, smaller %s layout with maxGap %s', (direction, maxGap) => {
    const original = layoutWith(undefined, direction);
    const compacted = layoutWith(maxGap, direction);

    expectValidLayout(compacted, direction);
    // Ranks stay put, and the layout only shrinks across them.
    const [rankAxis, size] =
      direction === 'horizontal' ? (['x', 'height'] as const) : (['y', 'width'] as const);
    expect(compacted[size]).toBeLessThanOrEqual(original[size]);
    for (const [id, node] of Object.entries(compacted.nodes)) {
      expect(node.bounds[rankAxis]).toEqual(original.nodes[id]?.bounds[rankAxis]);
    }
  });

  it('keeps the uncompacted layout if compaction throws', () => {
    // Move a box before throwing, so the test fails if partial results leak into the layout.
    const spy = jest.spyOn(CompactLayout, 'compactLayout').mockImplementation(({boxes}) => {
      for (const bounds of Object.values(boxes)) {
        bounds.y -= 1000;
      }
      throw new Error('boom');
    });
    const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    try {
      expect(layoutWith(250)).toEqual(layoutWith(undefined));
      expect(errorSpy).toHaveBeenCalled();
    } finally {
      spy.mockRestore();
      errorSpy.mockRestore();
    }
  });

  it('keeps single children level with their parent', () => {
    const layout = layoutWith(0);
    const centerY = (name: string) => {
      const bounds = layout.nodes[JSON.stringify([name])]?.bounds;
      return bounds ? bounds.y + bounds.height / 2 : NaN;
    };
    expect(centerY('c2')).toEqual(centerY('b2'));
    expect(centerY('c4')).toEqual(centerY('b4'));
  });
});
