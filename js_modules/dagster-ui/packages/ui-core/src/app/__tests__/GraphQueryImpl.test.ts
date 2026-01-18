import {calculateGraphDistances} from '../../asset-graph/useAssetGraphData';
import {GraphQueryItem, filterByQuery} from '../GraphQueryImpl';

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
