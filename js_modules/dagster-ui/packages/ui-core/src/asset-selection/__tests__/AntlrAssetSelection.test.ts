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

describe('parseAssetSelectionQuery', () => {
  it('should parse star query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, '*');
    expect(result.length).toBe(3);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B', 'C']));
  });

  it('should parse key query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'key:A');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');
  });

  it('should parse key_substring query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'key_substring:A');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');
  });

  it('should parse and query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'key:A and key:B');
    expect(result.length).toBe(0);
  });

  it('should parse or query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, 'key:A or key:B');
    expect(result.length).toBe(2);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B']));

    result = parseAssetSelectionQuery(TEST_GRAPH, '(key:A or key:B) and (key:B or key:C)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('B');
  });

  it('should parse upstream plus query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, '+key:A');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');

    result = parseAssetSelectionQuery(TEST_GRAPH, '+key:B');
    expect(result.length).toBe(2);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B']));

    result = parseAssetSelectionQuery(TEST_GRAPH, '++key:C');
    expect(result.length).toBe(3);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B', 'C']));
  });

  it('should parse downstream plus query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, 'key:C+');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('C');

    result = parseAssetSelectionQuery(TEST_GRAPH, 'key:B+');
    expect(result.length).toBe(2);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['B', 'C']));

    result = parseAssetSelectionQuery(TEST_GRAPH, 'key:A++');
    expect(result.length).toBe(3);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B', 'C']));
  });

  it('should parse upstream star query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, '*key:A');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');

    result = parseAssetSelectionQuery(TEST_GRAPH, '*key:C');
    expect(result.length).toBe(3);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B', 'C']));
  });

  it('should parse downstream star query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, 'key:C*');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('C');

    result = parseAssetSelectionQuery(TEST_GRAPH, 'key:A*');
    expect(result.length).toBe(3);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B', 'C']));
  });

  it('should parse sinks query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, 'sinks(*)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('C');

    result = parseAssetSelectionQuery(TEST_GRAPH, 'sinks(key:A)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');

    result = parseAssetSelectionQuery(TEST_GRAPH, 'sinks(key:B or key:B)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('B');
  });

  it('should parse roots query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, 'roots(*)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');

    result = parseAssetSelectionQuery(TEST_GRAPH, 'roots(key:C)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('C');

    result = parseAssetSelectionQuery(TEST_GRAPH, 'roots(key:B or key:C)');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('B');
  });

  it('should parse tag query', () => {
    let result = parseAssetSelectionQuery(TEST_GRAPH, 'tag:foo');
    expect(result.length).toBe(2);
    expect(new Set(result.map((r) => r.name))).toEqual(new Set(['A', 'B']));

    result = parseAssetSelectionQuery(TEST_GRAPH, 'tag:foo=bar');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');
  });

  it('should parse owner query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'owner:"owner@owner.com"');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');
  });

  it('should parse group query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'group:my_group');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('C');
  });

  it('should parse kind query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'kind:python');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('B');
  });

  it('should parse code location query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'code_location:"repo@my_location"');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('C');
  });
});
