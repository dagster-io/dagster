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
    {
      query: ' foo',
      expected: 'key:"*foo*"',
    },
    {
      query: '  key:a',
      expected: 'key:a',
    },
    {
      query: '  "foo"',
      expected: 'key:"*foo*"',
    },
    {
      query: '   ',
      expected: '',
    },
  ])('keeps the text intact when upgrading $query', ({query, expected}) => {
    expect(upgradeSyntax(query, 'key')).toBe(expected);
  });

  it.each([
    {query: 'dbt-model', attributeName: 'key', expected: 'key:"*dbt-model*"'},
    {query: '  dbt-model', attributeName: 'key', expected: 'key:"*dbt-model*"'},
    {query: 'not-x', attributeName: 'key', expected: 'key:"*not-x*"'},
    {query: 'a-b,c', attributeName: 'key', expected: 'key:"*a-b*" or key:"*c*"'},
    {
      query: 'name:alice@work foo',
      attributeName: 'name',
      expected: 'name:alice@work  or name:"*foo*"',
    },
    {query: 'key:a\u00a0,key:b', attributeName: 'key', expected: 'key:a\u00a0 or key:b'},
  ])('upgrades $query whole', ({query, attributeName, expected}) => {
    expect(upgradeSyntax(query, attributeName)).toBe(expected);
  });

  it.each([
    {reason: 'a value the grammar rejects', query: 'owner:ben@dagsterlabs.com'},
    {reason: 'a tag the grammar rejects', query: 'tag:a-b=c-d'},
    {reason: 'a hidden character in a value', query: 'key:a\u200b'},
    {reason: 'a lone keyword', query: 'and'},
    {reason: 'text after an unmatched parenthesis', query: 'key:a ) owner:ben'},
    {reason: 'a bare value with no letter or digit', query: 'key:a $ or key:b'},
    {reason: 'a bare value with a hidden character', query: 'foo\u200bbar'},
    {reason: 'an open quote before another term', query: '"a (key:b)'},
    {reason: 'terms touching a function call', query: 'my-func(key:a)'},
    {reason: 'terms touching a quoted value', query: '"a"-b'},
    {reason: 'a traversal count after a space', query: 'key:a+ 2'},
    {reason: 'a traversal count before a space', query: '2 +key:a'},
  ])('keeps $query as typed for $reason', ({query}) => {
    expect(upgradeSyntax(query, 'key')).toBe(query);
  });
});
