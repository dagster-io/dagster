import {upgradeSyntax} from '../syntaxUpgrader';

describe('upgradeSyntax', () => {
  it('should upgrade old syntax to new syntax', () => {
    expect(upgradeSyntax('value1,', 'key')).toBe('key:"*value1*" or ');
    expect(upgradeSyntax('value1, value2, value3', 'key')).toBe(
      'key:"*value1*" or key:"*value2*" or key:"*value3*"',
    );
    expect(upgradeSyntax('value1 value2', 'key')).toBe('key:"*value1*"  or key:"*value2*"');
    expect(upgradeSyntax('value1 or value2', 'key')).toBe('key:"*value1*" or key:"*value2*"');
    expect(upgradeSyntax('value1, value2', 'key')).toBe('key:"*value1*" or key:"*value2*"');
    expect(upgradeSyntax('key:value1 or key:value2  value2', 'key')).toBe(
      'key:value1 or key:value2   or key:"*value2*"',
    );
    expect(upgradeSyntax('value1 value2 key:value3', 'key')).toBe(
      'key:"*value1*"  or key:"*value2*"  or key:value3',
    );
  });

  it.each([
    {
      query: 'key:"😀", bar',
      expected: 'key:"😀" or key:"*bar*"',
    },
    {
      query: '"😀😀" foo',
      expected: 'key:"*😀😀*"  or key:"*foo*"',
    },
    {
      query: 'foo , bar',
      expected: 'key:"*foo*" or key:"*bar*"',
    },
    {
      query: 'key:a  , bar , baz',
      expected: 'key:a or key:"*bar*" or key:"*baz*"',
    },
  ])('keeps the text intact when upgrading $query', ({query, expected}) => {
    expect(upgradeSyntax(query, 'key')).toBe(expected);
  });
});
