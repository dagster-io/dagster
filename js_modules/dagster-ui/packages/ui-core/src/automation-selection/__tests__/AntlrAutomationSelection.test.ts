/* eslint-disable jest/expect-expect */

import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {parseAutomationSelectionQuery} from '../AntlrAutomationSelection';
import {Automation} from '../input/useAutomationSelectionAutoCompleteProvider';

const TEST_GRAPH: Automation[] = [
  {
    name: 'A',
    repo: {
      name: 'repo',
      location: 'location1',
    },
    type: 'schedule',
    status: 'running',
    tags: [{key: 'foo', value: 'bar'}, {key: 'foo'}],
  },
  {
    name: 'B',
    repo: {
      name: 'repo',
      location: 'location2',
    },
    type: 'schedule',
    status: 'running',
    tags: [{key: 'foo', value: 'bar'}, {key: 'foo'}],
  },
  {
    name: 'B2',
    repo: {
      name: 'repo',
      location: 'location2',
    },
    type: 'schedule',
    status: 'running',
    tags: [],
  },
  {
    name: 'C',
    repo: {
      name: 'repo',
      location: 'location1',
    },
    type: 'schedule',
    status: 'running',
    tags: [{key: 'foo', value: 'baz'}],
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseAutomationSelectionQuery(TEST_GRAPH, query);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(Array.from(result).map((automation) => automation.name))).toEqual(
    new Set(expectedNames),
  );
  expect(result.size).toBe(expectedNames.length);
}

// Most tests copied from AntlrAssetSelection.test.ts
describe('parseAutomationSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'A')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'name:A name:B')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'not')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'and')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'name:A and')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'notafunction()')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'tag:foo=')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'owner')).toBeInstanceOf(Error);
      expect(parseAutomationSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toBeInstanceOf(
        Error,
      );
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

    it('should parse type query', () => {
      assertQueryResult('type:schedule', ['A', 'B', 'B2', 'C']);
      assertQueryResult('type:sensor', []);
    });

    it('should parse status query', () => {
      assertQueryResult('status:running', ['A', 'B', 'B2', 'C']);
      assertQueryResult('status:stopped', []);
    });

    it('should parse tag query', () => {
      assertQueryResult('tag:foo=bar', ['A', 'B']);
      assertQueryResult('tag:foo=baz', ['C']);
    });

    it('should parse tag with null value', () => {
      assertQueryResult('tag:<null>', ['B2']);
    });
  });
});
