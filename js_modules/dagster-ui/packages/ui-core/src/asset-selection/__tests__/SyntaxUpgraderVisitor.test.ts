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
});
