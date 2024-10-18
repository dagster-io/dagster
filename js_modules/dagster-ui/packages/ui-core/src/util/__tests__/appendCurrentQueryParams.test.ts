import {appendCurrentQueryParams} from '../appendCurrentQueryParams';

describe('appendCurrentQueryParams', () => {
  // Backup the original window.location
  const originalLocation = window.location;

  beforeEach(() => {
    // Mock window.location
    delete (window as any).location;
    window.location = {
      origin: 'https://current-page.com',
      search: '?foo=1&bar=2',
    } as any;
  });

  afterAll(() => {
    // Restore the original window.location
    window.location = originalLocation;
  });

  it('appends current query params to a relative URL without query parameters', () => {
    const url = '/path';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/path?foo=1&bar=2');
  });

  it('appends current query params to an absolute URL without query parameters', () => {
    const url = 'https://example.com/path';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('https://example.com/path?foo=1&bar=2');
  });

  it('does not overwrite existing query parameters in the input URL', () => {
    const url = '/path?foo=3';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/path?foo=3&bar=2');
  });

  it('handles URLs with existing query parameters', () => {
    const url = '/path?baz=3';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/path?baz=3&foo=1&bar=2');
  });

  it('throws an error if the input URL is invalid', () => {
    const url = 'http://';
    expect(() => appendCurrentQueryParams(url)).toThrow('Invalid URL provided: http://');
  });

  it('returns relative URL if input URL is relative', () => {
    const url = 'path';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/path?foo=1&bar=2');
  });

  it('returns absolute URL if input URL is absolute', () => {
    const url = 'http://example.com/path';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('http://example.com/path?foo=1&bar=2');
  });

  it('does not append parameters that already exist in the input URL', () => {
    const url = 'http://example.com/path?foo=3&baz=4';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('http://example.com/path?foo=3&baz=4&bar=2');
  });

  it('handles empty current query parameters', () => {
    window.location.search = '';
    const url = '/path';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/path');
  });

  it('handles empty input URL', () => {
    const url = '';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/?foo=1&bar=2');
  });

  it('handles input URL that is just a query string', () => {
    const url = '?baz=3';
    const result = appendCurrentQueryParams(url);
    expect(result).toBe('/?baz=3&foo=1&bar=2');
  });

  it('appends array query parameters from current URL to input URL', () => {
    window.location.search = '?q[]=status:QUEUED&q[]=tag:user=marco@dagsterlabs.com';
    const url = '/runs-feed/b/fkeiyzer?tab=runs';
    const result = appendCurrentQueryParams(url);

    const expectedUrl =
      '/runs-feed/b/fkeiyzer?tab=runs&q%5B%5D=status%3AQUEUED&q%5B%5D=tag%3Auser%3Dmarco%40dagsterlabs.com';

    expect(decodeURIComponent(result)).toBe(decodeURIComponent(expectedUrl));
  });
});
