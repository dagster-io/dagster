import {isUnmatchedValueQuery} from '../isUnmatchedValueQuery';

describe('isUnmatchedValueQuery', () => {
  it('should return true for unmatched value queries', () => {
    expect(isUnmatchedValueQuery('key:"value"')).toBe(false);
    expect(isUnmatchedValueQuery('one two')).toBe(false);
    expect(isUnmatchedValueQuery('one')).toBe(true);
  });
});
