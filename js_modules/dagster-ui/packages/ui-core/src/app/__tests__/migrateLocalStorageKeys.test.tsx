import {migrateLocalStorageKeys} from '../migrateLocalStorageKeys';

describe('migrateLocalStorageKeys', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it('moves an existing value', () => {
    window.localStorage.setItem('foo', 'hello');
    expect(window.localStorage.getItem('foo')).toBe('hello');
    migrateLocalStorageKeys({from: /foo/gi, to: 'bar'});
    expect(window.localStorage.getItem('foo')).toBeNull();
    expect(window.localStorage.getItem('bar')).toBe('hello');
  });

  it('does not affect non-matching keys', () => {
    window.localStorage.setItem('foo', 'hello');
    expect(window.localStorage.getItem('foo')).toBe('hello');
    migrateLocalStorageKeys({from: /baz/gi, to: 'bar'});
    expect(window.localStorage.getItem('foo')).toBe('hello');
  });

  it('moves keys of various capitalization', () => {
    window.localStorage.setItem('FOO-COOL', 'lorem');
    window.localStorage.setItem('fOo-cOoL', 'ipsum');
    migrateLocalStorageKeys({from: /foo/gi, to: 'bar'});
    expect(window.localStorage.getItem('FOO-COOL')).toBeNull();
    expect(window.localStorage.getItem('fOo-cOoL')).toBeNull();
    expect(window.localStorage.getItem('bar-COOL')).toBe('lorem');
    expect(window.localStorage.getItem('bar-cOoL')).toBe('ipsum');
  });

  it('does not affect keys where the matching string is in the value', () => {
    window.localStorage.setItem('bar', 'foo');
    migrateLocalStorageKeys({from: /foo/gi, to: 'baz'});
    expect(window.localStorage.getItem('bar')).toBe('foo');
  });
});
