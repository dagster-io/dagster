/* eslint-disable jest/expect-expect */

import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {Job, parseJobSelectionQuery} from '../AntlrJobSelection';

const TEST_GRAPH: Job[] = [
  {
    name: 'A',
    repo: {
      name: 'repo',
      location: 'location1',
    },
  },
  {
    name: 'B',
    repo: {
      name: 'repo',
      location: 'location2',
    },
  },
  {
    name: 'B2',
    repo: {
      name: 'repo',
      location: 'location2',
    },
  },
  {
    name: 'C',
    repo: {
      name: 'repo',
      location: 'location1',
    },
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseJobSelectionQuery(TEST_GRAPH, query);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(Array.from(result.all).map((job) => job.name))).toEqual(new Set(expectedNames));
  expect(result.all.size).toBe(expectedNames.length);
}

// Most tests copied from AntlrAssetSelection.test.ts
describe('parseJobSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(parseJobSelectionQuery(TEST_GRAPH, 'A')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'name:A name:B')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'not')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'and')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'name:A and')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'notafunction()')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'tag:foo=')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'owner')).toBeInstanceOf(Error);
      expect(parseJobSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toBeInstanceOf(Error);
    });
  });

  describe('valid queries', () => {
    it('should parse star query', () => {
      assertQueryResult('*', ['A', 'B', 'B2', 'C']);
    });

    it('should parse name query', () => {
      assertQueryResult('name:A', ['A']);
    });

    it('should parse code location query', () => {
      assertQueryResult(`code_location:${buildRepoPathForHuman('repo', 'location1')}`, ['A', 'C']);
      assertQueryResult(`code_location:${buildRepoPathForHuman('repo', 'location2')}`, ['B', 'B2']);
    });

    it('should handle name wildcard queries', () => {
      assertQueryResult('name:*A*', ['A']);
      assertQueryResult('name:B*', ['B', 'B2']);
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
  });
});
