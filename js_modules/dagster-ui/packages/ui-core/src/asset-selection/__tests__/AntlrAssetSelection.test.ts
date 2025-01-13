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
    outputs: [{dependedBy: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
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
  {
    name: 'B2',
    node: buildAssetNode(),
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
    inputs: [{dependsOn: [{solid: {name: 'B'}}, {solid: {name: 'B2'}}]}],
    outputs: [{dependedBy: []}],
  },
];

function assertQueryResult(query: string, expectedNames: string[]) {
  const result = parseAssetSelectionQuery(TEST_GRAPH, query);
  expect(result).not.toBeInstanceOf(Error);
  if (result instanceof Error) {
    throw result;
  }
  expect(new Set(result.all.map((asset) => asset.name))).toEqual(new Set(expectedNames));
  expect(result.all.length).toBe(expectedNames.length);
}

describe('parseAssetSelectionQuery', () => {
  describe('invalid queries', () => {
    it('should throw on invalid queries', () => {
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'A')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'key:A key:B')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'not')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'and')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'key:A and')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'sinks')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'notafunction()')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'tag:foo=')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'owner')).toBeInstanceOf(Error);
      expect(parseAssetSelectionQuery(TEST_GRAPH, 'owner:owner@owner.com')).toBeInstanceOf(Error);
    });
  });

  describe('valid queries', () => {
    it('should parse star query', () => {
      assertQueryResult('*', ['A', 'B', 'B2', 'C']);
    });

    it('should parse key query', () => {
      assertQueryResult('key:A', ['A']);
    });

    it('should parse key_substring query', () => {
      assertQueryResult('key_substring:A', ['A']);
      assertQueryResult('key_substring:B', ['B', 'B2']);
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
      assertQueryResult('1+key:A', ['A']);
      assertQueryResult('1+key:B', ['A', 'B']);
      assertQueryResult('1+key:C', ['B', 'B2', 'C']);
      assertQueryResult('2+key:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream plus query', () => {
      assertQueryResult('key:A+1', ['A', 'B', 'B2']);
      assertQueryResult('key:A+2', ['A', 'B', 'B2', 'C']);
      assertQueryResult('key:C+1', ['C']);
      assertQueryResult('key:B+1', ['B', 'C']);
    });

    it('should parse upstream star query', () => {
      assertQueryResult('+key:A', ['A']);
      assertQueryResult('+key:B', ['A', 'B']);
      assertQueryResult('+key:C', ['A', 'B', 'B2', 'C']);
    });

    it('should parse downstream star query', () => {
      assertQueryResult('key:A+', ['A', 'B', 'B2', 'C']);
      assertQueryResult('key:B+', ['B', 'C']);
      assertQueryResult('key:C+', ['C']);
    });

    it('should parse up and down traversal queries', () => {
      assertQueryResult('key:A+ and +key:C', ['A', 'B', 'B2', 'C']);
      assertQueryResult('+key:B+', ['A', 'B', 'C']);
      assertQueryResult('key:A+ and +key:C and +key:B+', ['A', 'B', 'C']);
      assertQueryResult('key:A+ and +key:B+ and +key:C', ['A', 'B', 'C']);
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
