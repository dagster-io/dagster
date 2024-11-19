import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {buildAssetNode} from '../../graphql/types';
import {parseAssetSelectionQuery} from '../AntlrAssetSelection';

const TEST_GRAPH: AssetGraphQueryItem[] = [
  // Top Layer
  {
    name: 'A',
    node: buildAssetNode({
      tags: [{__typename: 'DefinitionTag', key: 'foo', value: 'bar'}],
      owners: [{__typename: 'UserAssetOwner', email: 'owner@owner.com'}],
    }),
    inputs: [{dependsOn: []}],
    outputs: [{dependedBy: [{solid: {name: 'B'}}]}],
  },
  // Second Layer
  {
    name: 'B',
    node: buildAssetNode({
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
    }),
    inputs: [{dependsOn: [{solid: {name: 'B'}}]}],
    outputs: [{dependedBy: []}],
  },
];

describe('parseAssetSelectionQuery', () => {
  it('should parse a simple query', () => {
    const result = parseAssetSelectionQuery(TEST_GRAPH, 'key:A');
    expect(result.length).toBe(1);
    expect(result[0]!.name).toBe('A');
  });
});
