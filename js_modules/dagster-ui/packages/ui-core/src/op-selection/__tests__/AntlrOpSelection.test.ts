/* eslint-disable jest/expect-expect */

import {GraphQueryItem} from '../../app/GraphQueryImpl';
import {parseOpSelectionQuery} from '../AntlrOpSelection';

const TEST_GRAPH: GraphQueryItem[] = [
  // Top Layer
  {
    name: 'A',
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
  },
  // Second Layer
  {
    name: 'B',
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },
  {
    name: 'B2',
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },
  // Third Layer
  {
    name: 'C',
    inputs: [{dependsOn: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
    outputs: [{dependedBy: []}],
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseOpSelectionQuery(TEST_GRAPH, query);
  expect(result).not.toBeInstanceOf(Error);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(result.all.map((op) => op.name))).toEqual(new Set(expectedNames));
  expect(result.all.length).toBe(expectedNames.length);
}

// Most tests copied from AntlrAssetSelection.test.ts
describe('parseOpSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(parseOpSelectionQuery(TEST_GRAPH, 'A')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'name:A name:B')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'not')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'and')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'name:A and')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'notafunction()')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'tag:foo=')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'owner')).toBeInstanceOf(Error);
      expect(parseOpSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toBeInstanceOf(Error);
    });
  });

  describe('valid queries', () => {
    it('should parse star query', () => {
      assertQueryResult('*', ['A', 'B', 'B2', 'C']);
    });

    it('should parse name query', () => {
      assertQueryResult('name:A', ['A']);
    });

    it('should parse name_substring query', () => {
      assertQueryResult('name_substring:A', ['A']);
      assertQueryResult('name_substring:B', ['B', 'B2']);
    });

    it('should parse and query', () => {
      assertQueryResult('name:A and name:B', []);
      assertQueryResult('name:A and name:B and name:C', []);
    });

    it('should parse or query', () => {
      assertQueryResult('name:A or name:B', ['A', 'B']);
      assertQueryResult('name:A or name:B or name:C', ['A', 'B', 'C']);
      assertQueryResult('(name:A or name:B) and (name:B or name:C)', ['B']);
    });

    it('should parse upstream plus query', () => {
      assertQueryResult('1+name:A', ['A']);
      assertQueryResult('1+name:B', ['A', 'B']);
      assertQueryResult('1+name:C', ['B', 'B2', 'C']);
      assertQueryResult('2+name:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream plus query', () => {
      assertQueryResult('name:A+1', ['A', 'B', 'B2']);
      assertQueryResult('name:A+2', ['A', 'B', 'B2', 'C']);
      assertQueryResult('name:C+1', ['C']);
      assertQueryResult('name:B+1', ['B', 'C']);
    });

    it('should parse upstream star query', () => {
      assertQueryResult('+name:A', ['A']);
      assertQueryResult('+name:B', ['A', 'B']);
      assertQueryResult('+name:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream star query', () => {
      assertQueryResult('name:A+', ['A', 'B', 'B2', 'C']);
      assertQueryResult('name:B+', ['B', 'C']);
      assertQueryResult('name:C+', ['C']);
    });

    it('should parse up and down traversal queries', () => {
      assertQueryResult('name:A+ and +name:C', ['A', 'B', 'B2', 'C']);
      assertQueryResult('+name:B+', ['A', 'B', 'C']);
      assertQueryResult('name:A+ and +name:C and +name:B+', ['A', 'B', 'C']);
      assertQueryResult('name:A+ and +name:B+ and +name:C', ['A', 'B', 'C']);
    });

    it('should handle sinks and roots', () => {
      assertQueryResult('*', ['A', 'B', 'B2', 'C']);
      assertQueryResult('roots(*)', ['A']);
      assertQueryResult('sinks(*)', ['C']);
    });
  });
});
