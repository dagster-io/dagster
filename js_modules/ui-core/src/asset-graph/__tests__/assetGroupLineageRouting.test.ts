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

  it('finds sibling and cousin common ancestors', () => {
    const index = buildGroupAncestryIndex({
      root: null,
      left: 'root',
      'left/one': 'left',
      'left/two': 'left',
      right: 'root',
      'right/one': 'right',
    });

    expect(index.lowestCommonAncestor('left/one', 'left/two')).toBe('left');
    expect(index.lowestCommonAncestor('left/one', 'right/one')).toBe('root');
  });

  it('handles roots, identical groups, and non-ancestor branches', () => {
    const index = buildGroupAncestryIndex({
      root: null,
      left: 'root',
      'left/leaf': 'left',
      right: 'root',
    });

    expect(index.lowestCommonAncestor('root', 'root')).toBe('root');
    expect(index.lowestCommonAncestor('left/leaf', 'left/leaf')).toBe('left/leaf');
    expect(index.branchBelow('root', 'root')).toBe(null);
    expect(index.branchBelow('left/leaf', 'right')).toBe(null);
  });

  it('rejects missing parents and unknown lookup groups', () => {
    expect(() => buildGroupAncestryIndex({child: 'missing'})).toThrow(
      'Missing visible asset group parent: missing',
    );

    const index = buildGroupAncestryIndex({root: null});
    expect(() => index.lowestCommonAncestor('root', 'missing')).toThrow(
      'Unknown visible asset group: missing',
    );
    expect(() => index.branchBelow('root', 'missing')).toThrow(
      'Unknown visible asset group: missing',
    );
  });

  it('indexes deep hierarchies without recursive stack growth', () => {
    const parentById: Record<string, string | null> = {};
    const groupId = (index: number) => `group-${index.toString().padStart(5, '0')}`;
    const groupCount = 20_000;
    for (let index = 0; index < groupCount; index++) {
      parentById[groupId(index)] = index === 0 ? null : groupId(index - 1);
    }

    const index = buildGroupAncestryIndex(parentById);
    expect(index.lowestCommonAncestor(groupId(groupCount - 1), groupId(10_000))).toBe(
      groupId(10_000),
    );
    expect(index.branchBelow(groupId(groupCount - 1), groupId(0))).toBe(groupId(1));
  });
});
