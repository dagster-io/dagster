import {assertExists, invariant} from '../invariant';

describe('invariant', () => {
  test('passes when condition is truthy', () => {
    expect(() => invariant(true)).not.toThrow();
    expect(() => invariant(1)).not.toThrow();
    expect(() => invariant('string')).not.toThrow();
    expect(() => invariant({})).not.toThrow();
    expect(() => invariant([])).not.toThrow();
  });

  test('throws when condition is falsy', () => {
    expect(() => invariant(false)).toThrow('Invariant violation');
    expect(() => invariant(null)).toThrow('Invariant violation');
    expect(() => invariant(undefined)).toThrow('Invariant violation');
    expect(() => invariant(0)).toThrow('Invariant violation');
    expect(() => invariant('')).toThrow('Invariant violation');
  });

  test('includes custom message when provided', () => {
    expect(() => invariant(false, 'Custom error message')).toThrow('Custom error message');
  });
});

describe('assertExists', () => {
  test('returns value when not null or undefined', () => {
    expect(assertExists('value')).toBe('value');
    expect(assertExists(0)).toBe(0);
    expect(assertExists(false)).toBe(false);
    expect(assertExists('')).toBe('');
    expect(assertExists({})).toEqual({});
    expect(assertExists([])).toEqual([]);
  });

  test('throws when value is null', () => {
    expect(() => assertExists(null)).toThrow('Expected value to exist');
  });

  test('throws when value is undefined', () => {
    expect(() => assertExists(undefined)).toThrow('Expected value to exist');
  });

  test('includes custom message when provided', () => {
    expect(() => assertExists(null, 'Value must not be null')).toThrow('Value must not be null');
    expect(() => assertExists(undefined, 'Value is required')).toThrow('Value is required');
  });
});
