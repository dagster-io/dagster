import {GraphData} from '../Utils';
import {layoutAssetGraph} from '../layout';

const assetId = (name: string) => JSON.stringify([name]);

const graphOf = (names: string[], edges: [string, string][] = []): GraphData => {
  const data: GraphData = {nodes: {}, downstream: {}, upstream: {}};
  for (const name of names) {
    const id = assetId(name);
    data.nodes[id] = {
      id,
      assetKey: {path: [name]},
      definition: {groupName: null, repository: {name: 'repo', location: {name: 'loc'}}},
    } as any;
  }
  for (const [from, to] of edges) {
    data.downstream[assetId(from)] = {...data.downstream[assetId(from)], [assetId(to)]: true};
    data.upstream[assetId(to)] = {...data.upstream[assetId(to)], [assetId(from)]: true};
  }
  return data;
};

const graphWithOrphans = (count: number) =>
  graphOf(Array.from({length: count}, (_, i) => `asset_${i}`));

const layout = (data: GraphData) =>
  layoutAssetGraph(data, {
    direction: 'horizontal',
    facets: [],
    flagAssetGraphGroupsPerCodeLocation: false,
  });

describe('layoutAssetGraph', () => {
  it('spreads unconnected assets into a grid and draws no edges between them', () => {
    const result = layout(graphWithOrphans(16));
    const xs = new Set(Object.values(result.nodes).map((n) => n.bounds.x));
    const ys = new Set(Object.values(result.nodes).map((n) => n.bounds.y));
    expect(xs.size).toBe(4);
    expect(ys.size).toBe(4);
    expect(result.edges).toEqual([]);
  });

  it('spreads the fan-out of one source into many copies into a grid, keeping the real edges', () => {
    const copies = Array.from({length: 16}, (_, i) => `copy_${i}`);
    const result = layout(
      graphOf(
        ['source', ...copies],
        copies.map((c) => ['source', c]),
      ),
    );
    const copyXs = new Set(copies.map((c) => result.nodes[assetId(c)]?.bounds.x));
    expect(copyXs.size).toBe(4);
    expect(result.edges).toHaveLength(16);
    expect(result.edges.every((e) => e.fromId === assetId('source'))).toBe(true);
  });

  it('leaves a handful of unconnected assets in one column', () => {
    const result = layout(graphWithOrphans(3));
    const xs = new Set(Object.values(result.nodes).map((n) => n.bounds.x));
    expect(xs.size).toBe(1);
  });
});
