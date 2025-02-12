import {GraphQueryItem, filterByQuery} from '../GraphQueryImpl';

function mockQueryItem(name: string, dependsOn: string[], dependedBy: string[]): GraphQueryItem {
  return {
    name,
    inputs: [{dependsOn: dependsOn.map((name) => ({solid: {name}}))}],
    outputs: [{dependedBy: dependedBy.map((name) => ({solid: {name}}))}],
  };
}

describe('filterByQuery', () => {
  it('should properly traverse graphs with shortcuts', () => {
    const graph = [
      mockQueryItem('A', ['B', 'C'], []),
      mockQueryItem('B', ['C'], ['A']),
      mockQueryItem('C', ['D'], ['A', 'B']),
      mockQueryItem('D', ['E'], ['C']),
      mockQueryItem('E', [], ['D']),
    ];
    expect(filterByQuery(graph, 'A').all.map((a) => a.name)).toEqual(['A']);
    expect(filterByQuery(graph, '+A').all.map((a) => a.name)).toEqual(['A', 'B', 'C']);
    expect(filterByQuery(graph, '++A').all.map((a) => a.name)).toEqual(['A', 'B', 'C', 'D']);
  });
});
