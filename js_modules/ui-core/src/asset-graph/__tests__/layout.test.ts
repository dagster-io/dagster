import {GraphData} from '../Utils';
import {layoutAssetGraph} from '../layout';

const graphWithOrphans = (count: number): GraphData => {
  const nodes: GraphData['nodes'] = {};
  for (let i = 0; i < count; i++) {
    const id = JSON.stringify([`asset_${i}`]);
    nodes[id] = {
      id,
      assetKey: {path: [`asset_${i}`]},
      definition: {groupName: null, repository: {name: 'repo', location: {name: 'loc'}}},
    } as any;
  }
  return {nodes, downstream: {}, upstream: {}};
};

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

  it('leaves a handful of unconnected assets in one column', () => {
    const result = layout(graphWithOrphans(3));
    const xs = new Set(Object.values(result.nodes).map((n) => n.bounds.x));
    expect(xs.size).toBe(1);
  });
});
