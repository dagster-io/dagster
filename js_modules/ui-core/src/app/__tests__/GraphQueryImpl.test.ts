import {calculateGraphDistances} from '../../asset-graph/useAssetGraphData';
import {assertExists} from '../../util/invariant';
import {GraphQueryItem, GraphTraverser, filterByQuery} from '../GraphQueryImpl';

function mockQueryItem(name: string, dependsOn: string[], dependedBy: string[]): GraphQueryItem {
  return {
    name,
    inputs: [{dependsOn: dependsOn.map((name) => ({solid: {name}}))}],
    outputs: [{dependedBy: dependedBy.map((name) => ({solid: {name}}))}],
  };
}

// E -> D -> C -> B -> A
//           C ------> A
const graph = [
  mockQueryItem('A', ['B', 'C'], []),
  mockQueryItem('B', ['C'], ['A']),
  mockQueryItem('C', ['D'], ['A', 'B']),
  mockQueryItem('D', ['E'], ['C']),
  mockQueryItem('E', [], ['D']),
];

describe('filterByQuery', () => {
  it('should properly resolve traversal operators', () => {
    expect(filterByQuery(graph, 'A').all.map((a) => a.name)).toEqual(['A']);
    expect(filterByQuery(graph, '+A').all.map((a) => a.name)).toEqual(['A', 'B', 'C']);
    expect(filterByQuery(graph, '*A').all.map((a) => a.name)).toEqual(['A', 'B', 'C', 'D', 'E']);
    expect(filterByQuery(graph, '+C+').all.map((a) => a.name)).toEqual(['C', 'D', 'A', 'B']);
  });
  it('should properly traverse graphs with shortcuts', () => {
    // D is included only because of A -> C -> D, if you visited it via depth-first search
    // you'd hit A -> B -> C -> D and mark C as visited at depth = 2
    expect(filterByQuery(graph, '++A').all.map((a) => a.name)).toEqual(['A', 'B', 'C', 'D']);
  });
});

describe('calculateGraphDistances', () => {
  it('should correctly determine the total depths from a node', () => {
    expect(calculateGraphDistances(graph, {path: ['A']})).toEqual({
      upstream: 3,
      downstream: 0,
    });
    expect(calculateGraphDistances(graph, {path: ['C']})).toEqual({
      upstream: 2,
      downstream: 1,
    });
  });
});

// `layers` stacked diamonds: each layer has two items that both feed both items in the next layer.
function stackedDiamonds(layers: number) {
  const name = (layer: number, i: number) => `L${layer}_${i}`;
  const items: GraphQueryItem[] = [];
  for (let layer = 0; layer < layers; layer++) {
    for (const i of [0, 1]) {
      const parents = layer === 0 ? [] : [name(layer - 1, 0), name(layer - 1, 1)];
      const children = layer === layers - 1 ? [] : [name(layer + 1, 0), name(layer + 1, 1)];
      items.push(mockQueryItem(name(layer, i), parents, children));
    }
  }
  return items;
}

describe('GraphTraverser', () => {
  it('expands each item once on graphs with fan-in', () => {
    const items = stackedDiamonds(20);
    const traverser = new GraphTraverser(items);
    const expanded: string[] = [];
    const result = traverser.traverse(
      assertExists(items[0]),
      (item, callback) => {
        expanded.push(item.name);
        item.outputs.forEach((o) =>
          o.dependedBy.forEach((d) => {
            const next = traverser.itemNamed(d.solid.name);
            if (next) {
              callback(next);
            }
          }),
        );
      },
      Number.MAX_SAFE_INTEGER,
    );
    expect(result).toHaveLength(items.length - 1);
    expect(expanded).toHaveLength(items.length - 1);
  });

  it('applies the depth limit from the nearest root when given several', () => {
    const traverser = new GraphTraverser(graph);
    const byName = (name: string) =>
      assertExists(traverser.itemNamed(name), `No fixture named ${name}`);
    const names = (items: GraphQueryItem[]) => items.map((i) => i.name).sort();

    expect(names(traverser.fetchUpstream([byName('A'), byName('D')], 1))).toEqual([
      'A',
      'B',
      'C',
      'D',
      'E',
    ]);
    expect(names(traverser.fetchDownstream([byName('E'), byName('B')], 1))).toEqual([
      'A',
      'B',
      'D',
      'E',
    ]);
  });

  it('finds sinks and roots through unselected items', () => {
    const traverser = new GraphTraverser(graph);
    const select = (...names: string[]) =>
      new Set(names.map((n) => assertExists(traverser.itemNamed(n), `No fixture named ${n}`)));
    const names = (items: Set<GraphQueryItem>) => [...items].map((i) => i.name).sort();

    // E -> D -> C, with D unselected
    expect(names(traverser.sinks(select('E', 'C')))).toEqual(['C']);
    expect(names(traverser.roots(select('E', 'C')))).toEqual(['E']);
    expect(names(traverser.sinks(select('B', 'C')))).toEqual(['B']);
    expect(names(traverser.roots(select('A', 'B')))).toEqual(['B']);
    expect(names(traverser.sinks(new Set(graph)))).toEqual(['A']);
    expect(names(traverser.roots(new Set(graph)))).toEqual(['E']);
  });

  it('finds sinks and roots on graphs with fan-in', () => {
    const items = stackedDiamonds(20);
    const traverser = new GraphTraverser(items);
    const names = (items: Set<GraphQueryItem>) => [...items].map((i) => i.name).sort();

    expect(names(traverser.sinks(new Set(items)))).toEqual(['L19_0', 'L19_1']);
    expect(names(traverser.roots(new Set(items)))).toEqual(['L0_0', 'L0_1']);
  });
});

describe('GraphTraverser against a brute-force reference', () => {
  function rng(seed: number) {
    return () => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };
  }

  // Random DAG (edges only go from lower to higher index) with fan-in and self-edges, which
  // self-dependent partitioned assets produce. Items are returned in shuffled order.
  function randomGraph(rand: () => number) {
    const n = 1 + Math.floor(rand() * 25);
    const density = rand() * 0.4;
    const parents: string[][] = Array.from({length: n}, () => []);
    const children: string[][] = Array.from({length: n}, () => []);
    for (let i = 0; i < n; i++) {
      for (let j = i; j < n; j++) {
        if (i === j ? rand() < 0.15 : rand() < density) {
          children[i]?.push(`n${j}`);
          parents[j]?.push(`n${i}`);
        }
      }
    }
    const items = parents.map((p, i) => mockQueryItem(`n${i}`, p, children[i] ?? []));
    return items.sort(() => rand() - 0.5);
  }

  // Expands one step at a time from each root separately, then unions the results.
  function reachableWithin(
    items: GraphQueryItem[],
    roots: string[],
    depth: number,
    direction: 'up' | 'down',
  ) {
    const byName = new Map(items.map((i) => [i.name, i]));
    const neighbors = (name: string) => {
      const item = byName.get(name);
      if (!item) {
        return [];
      }
      return direction === 'up'
        ? item.inputs.flatMap((i) => i.dependsOn.map((d) => d.solid.name))
        : item.outputs.flatMap((o) => o.dependedBy.map((d) => d.solid.name));
    };
    const result = new Set<string>();
    for (const root of roots) {
      let reached = new Set([root]);
      for (let step = 0; step < Math.min(depth, items.length); step++) {
        reached = new Set([...reached, ...[...reached].flatMap(neighbors)]);
      }
      reached.forEach((name) => result.add(name));
    }
    return result;
  }

  // Selected items with no *other* selected item downstream (or upstream).
  function bruteForceEnds(items: GraphQueryItem[], selected: string[], direction: 'up' | 'down') {
    const selectedSet = new Set(selected);
    return selected.filter((name) => {
      const item = items.find((i) => i.name === name);
      if (!item) {
        return false;
      }
      const firstStep =
        direction === 'down'
          ? item.outputs.flatMap((o) => o.dependedBy.map((d) => d.solid.name))
          : item.inputs.flatMap((i) => i.dependsOn.map((d) => d.solid.name));
      const reachable = reachableWithin(items, firstStep, items.length, direction);
      return ![...reachable].some((other) => other !== name && selectedSet.has(other));
    });
  }

  const sorted = (names: Iterable<string>) => [...names].sort();

  it('matches the reference on random graphs, selections and depths', () => {
    const rand = rng(1);
    for (let trial = 0; trial < 500; trial++) {
      const items = randomGraph(rand);
      const traverser = new GraphTraverser(items);
      const selected = items.filter(() => rand() < 0.3);
      const selectedNames = selected.map((i) => i.name);
      const depth = [0, 1, 2, 3, Number.MAX_SAFE_INTEGER][Math.floor(rand() * 5)] ?? 0;
      const context = `trial ${trial}, depth ${depth}, selected ${selectedNames.join(',')}`;

      expect([
        context,
        sorted(traverser.fetchUpstream(selected, depth).map((i) => i.name)),
      ]).toEqual([context, sorted(reachableWithin(items, selectedNames, depth, 'up'))]);
      expect([
        context,
        sorted(traverser.fetchDownstream(selected, depth).map((i) => i.name)),
      ]).toEqual([context, sorted(reachableWithin(items, selectedNames, depth, 'down'))]);

      const selection = new Set(selected);
      expect([context, sorted([...traverser.sinks(selection)].map((i) => i.name))]).toEqual([
        context,
        sorted(bruteForceEnds(items, selectedNames, 'down')),
      ]);
      expect([context, sorted([...traverser.roots(selection)].map((i) => i.name))]).toEqual([
        context,
        sorted(bruteForceEnds(items, selectedNames, 'up')),
      ]);
    }
  });

  it('keeps self-dependent items as sinks and roots', () => {
    // B depends on an earlier partition of itself
    const items = [
      mockQueryItem('A', [], ['B']),
      mockQueryItem('B', ['A', 'B'], ['B', 'C']),
      mockQueryItem('C', ['B'], []),
    ];
    const traverser = new GraphTraverser(items);
    const select = (...names: string[]) =>
      new Set(names.map((n) => assertExists(traverser.itemNamed(n), `No fixture named ${n}`)));
    const names = (items: Set<GraphQueryItem>) => [...items].map((i) => i.name).sort();

    expect(names(traverser.sinks(select('B')))).toEqual(['B']);
    expect(names(traverser.roots(select('B')))).toEqual(['B']);
    expect(names(traverser.sinks(select('A', 'B')))).toEqual(['B']);
    expect(names(traverser.roots(select('B', 'C')))).toEqual(['B']);
  });

  it('terminates on cycles', () => {
    const a = mockQueryItem('A', ['C'], ['B']);
    const items = [a, mockQueryItem('B', ['A'], ['C']), mockQueryItem('C', ['B'], ['A'])];
    const traverser = new GraphTraverser(items);
    const names = (items: GraphQueryItem[]) => items.map((i) => i.name).sort();
    expect(names(traverser.fetchDownstream(a, Number.MAX_SAFE_INTEGER))).toEqual(['A', 'B', 'C']);
  });
});
