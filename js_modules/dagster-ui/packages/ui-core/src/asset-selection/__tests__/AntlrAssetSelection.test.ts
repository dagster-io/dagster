/* eslint-disable jest/expect-expect */
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {
  buildAssetNode,
  buildDefinitionTag,
  buildRepository,
  buildRepositoryLocation,
  buildUserAssetOwner,
} from '../../graphql/types';
import {parseAssetSelectionQuery} from '../AntlrAssetSelection';

const TEST_GRAPH: AssetGraphQueryItem[] = [
  // Top Layer
  {
    name: 'A',
    node: buildAssetNode({
      tags: [buildDefinitionTag({key: 'foo', value: 'bar'})],
      owners: [buildUserAssetOwner({email: 'owner@owner.com'})],
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'B'}}]}],
  },
  // Second Layer
  {
    name: 'B',
    node: buildAssetNode({
      tags: [buildDefinitionTag({key: 'foo', value: 'baz'})],
      kinds: ['python', 'snowflake'],
    }),
    inputs: [{dependsOn: [{solid: {name: 'A'}}]}],
    outputs: [{dependedBy: [{solid: {name: 'C'}}]}],
  },

  // Third Layer
  {
    name: 'C',
    node: buildAssetNode({
      groupName: 'my_group',
      repository: buildRepository({
        name: 'repo',
        location: buildRepositoryLocation({name: 'my_location'}),
      }),
    }),
    inputs: [{dependsOn: [{solid: {name: 'B'}}]}],
    outputs: [{dependedBy: []}],
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseAssetSelectionQuery(TEST_GRAPH, query);
  expect(result.length).toBe(expectedNames.length);
  expect(new Set(result.map((r) => r.name))).toEqual(new Set(expectedNames));
}

describe('parseAssetSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'A')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'key:A key:B')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'not')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'and')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'key:A and')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'sinks')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'notafunction()')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'tag:foo=')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'owner')).toThrow();
      expect(() => parseAssetSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toThrow();
    });
  });

  describe('valid queries', () => {
    it('should parse star query', () => {
      assertQueryResult('*', ['A', 'B', 'C']);
    });

    it('should parse key query', () => {
      assertQueryResult('key:A', ['A']);
    });

    it('should parse key_substring query', () => {
      assertQueryResult('key:A', ['A']);
    });

    it('should parse and query', () => {
      assertQueryResult('key:A and key:B', []);
      assertQueryResult('key:A and key:B and key:C', []);
    });

    it('should parse or query', () => {
      assertQueryResult('key:A or key:B', ['A', 'B']);
      assertQueryResult('key:A or key:B or key:C', ['A', 'B', 'C']);
      assertQueryResult('(key:A or key:B) and (key:B or key:C)', ['B']);
    });

    it('should parse upstream plus query', () => {
      assertQueryResult('+key:A', ['A']);
      assertQueryResult('+key:B', ['A', 'B']);
      assertQueryResult('++key:C', ['A', 'B', 'C']);
    });

    it('should parse downstream plus query', () => {
      assertQueryResult('key:C+', ['C']);
      assertQueryResult('key:B+', ['B', 'C']);
      assertQueryResult('key:A++', ['A', 'B', 'C']);
    });

    it('should parse upstream star query', () => {
      assertQueryResult('*key:A', ['A']);
      assertQueryResult('*key:B', ['A', 'B']);
      assertQueryResult('**key:C', ['A', 'B', 'C']);
    });

    it('should parse downstream star query', () => {
      assertQueryResult('key:C*', ['C']);
      assertQueryResult('key:B*', ['B', 'C']);
      assertQueryResult('key:A**', ['A', 'B', 'C']);
    });

    it('should parse sinks query', () => {
      assertQueryResult('sinks(*)', ['C']);
      assertQueryResult('sinks(key:A)', ['A']);
      assertQueryResult('sinks(key:A or key:B)', ['B']);
    });

    it('should parse roots query', () => {
      assertQueryResult('roots(*)', ['A']);
      assertQueryResult('roots(key:C)', ['C']);
      assertQueryResult('roots(key:A or key:B)', ['A']);
    });

    it('should parse tag query', () => {
      assertQueryResult('tag:foo', ['A', 'B']);
      assertQueryResult('tag:foo=bar', ['A']);
    });

    it('should parse owner query', () => {
      assertQueryResult('owner:"owner@owner.com"', ['A']);
    });

    it('should parse group query', () => {
      assertQueryResult('group:my_group', ['C']);
    });

    it('should parse kind query', () => {
      assertQueryResult('kind:python', ['B']);
      assertQueryResult('kind:snowflake', ['B']);
    });

    it('should parse code location query', () => {
      assertQueryResult('code_location:"repo@my_location"', ['C']);
    });
  });
});
