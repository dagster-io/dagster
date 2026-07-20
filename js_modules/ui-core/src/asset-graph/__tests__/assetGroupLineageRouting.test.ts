import {buildGroupAncestryIndex} from '../assetGroupLineageRouting';

describe('buildGroupAncestryIndex', () => {
  it('finds common ancestors and branches below ancestors', () => {
    const index = buildGroupAncestryIndex({
      source: null,
      'source/inner': 'source',
      'source/inner/leaf': 'source/inner',
      target: null,
      'target/leaf': 'target',
    });

    expect(index.lowestCommonAncestor('source/inner', 'source/inner/leaf')).toBe(
      'source/inner',
    );
    expect(index.lowestCommonAncestor('source/inner/leaf', 'target/leaf')).toBe(null);
    expect(index.branchBelow('source/inner/leaf', 'source')).toBe('source/inner');
    expect(index.branchBelow('target/leaf', null)).toBe('target');
  });

  it('rejects cycles in the visible asset group parent hierarchy', () => {
    expect(() => buildGroupAncestryIndex({a: 'b', b: 'a'})).toThrow(
      'Asset group parent cycle',
    );
  });
});
