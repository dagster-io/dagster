import {tokenizeString} from './TokenizingField';

describe('tokenizeString', () => {
  it('tokenizes when there is only a token', () => {
    expect(tokenizeString('foo')).toEqual(['foo', '']);
  });

  it('tokenizes when there is a token and value', () => {
    expect(tokenizeString('foo:bar')).toEqual(['foo', 'bar']);
  });

  it('tokenizes when there is only a value with colons in it', () => {
    expect(tokenizeString('foo:bar:baz')).toEqual(['foo', 'bar:baz']);
  });
});
