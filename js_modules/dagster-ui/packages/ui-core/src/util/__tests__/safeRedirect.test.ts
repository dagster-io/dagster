import {isSafeUrl, safeRedirect} from '../safeRedirect';

describe('isSafeUrl', () => {
  describe('allows safe URLs', () => {
    test('simple relative path', () => {
      expect(isSafeUrl('/foo')).toBe(true);
    });

    test('relative path with query params', () => {
      expect(isSafeUrl('/assets?asset-selection=kind%3A%22snowflake%22')).toBe(true);
    });

    test('relative path with hash', () => {
      expect(isSafeUrl('/page#section')).toBe(true);
    });

    test('root path', () => {
      expect(isSafeUrl('/')).toBe(true);
    });

    test('deeply nested path', () => {
      expect(isSafeUrl('/org/deployment/assets/some-asset')).toBe(true);
    });

    test('https URL', () => {
      expect(isSafeUrl('https://dagster.cloud/login?next=%2Fassets')).toBe(true);
    });

    test('http URL', () => {
      expect(isSafeUrl('http://localhost:3000/login')).toBe(true);
    });
  });

  describe('blocks unsafe URLs', () => {
    test('javascript: protocol', () => {
      expect(isSafeUrl('javascript:alert(1)')).toBe(false);
    });

    test('javascript: with mixed case', () => {
      expect(isSafeUrl('JavaScript:alert(1)')).toBe(false);
    });

    test('data: protocol', () => {
      expect(isSafeUrl('data:text/html,<script>alert(1)</script>')).toBe(false);
    });

    test('vbscript: protocol', () => {
      expect(isSafeUrl('vbscript:msgbox("xss")')).toBe(false);
    });

    test('protocol-relative URL (//)', () => {
      expect(isSafeUrl('//evil.com/path')).toBe(false);
    });

    test('empty string', () => {
      expect(isSafeUrl('')).toBe(false);
    });

    test('bare domain string', () => {
      expect(isSafeUrl('evil.com')).toBe(false);
    });

    test('javascript: with leading whitespace', () => {
      expect(isSafeUrl('\tjavascript:alert(1)')).toBe(false);
    });

    test('ftp: protocol', () => {
      expect(isSafeUrl('ftp://example.com/file')).toBe(false);
    });

    test('file: protocol', () => {
      expect(isSafeUrl('file:///etc/passwd')).toBe(false);
    });
  });
});

describe('safeRedirect', () => {
  const originalLocation = window.location;
  let hrefSetter: jest.Mock;

  beforeEach(() => {
    hrefSetter = jest.fn();
    // @ts-expect-error - overriding read-only property for testing
    delete window.location;
    window.location = {...originalLocation, href: ''} as Location;
    Object.defineProperty(window.location, 'href', {
      set: hrefSetter,
      get: () => '',
      configurable: true,
    });
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  test('navigates for a safe URL', () => {
    safeRedirect('/foo');
    expect(hrefSetter).toHaveBeenCalledWith('/foo');
  });

  test('does not navigate for an unsafe URL', () => {
    safeRedirect('javascript:alert(1)');
    expect(hrefSetter).not.toHaveBeenCalled();
  });
});
