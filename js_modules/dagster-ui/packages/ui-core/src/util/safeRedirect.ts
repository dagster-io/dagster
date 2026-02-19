/**
 * Safely set window.location.href, guarding against javascript: and other
 * dangerous protocols. Allows http/https absolute URLs and relative paths.
 */
export function safeRedirect(url: string): void {
  if (isSafeUrl(url)) {
    window.location.href = url;
  } else if (process.env.NODE_ENV === 'development') {
    console.error(`Blocked unsafe redirect to: ${url}`);
  }
}

export function isSafeUrl(url: string): boolean {
  // Relative paths starting with "/" (but not "//", which is protocol-relative)
  if (url.startsWith('/') && !url.startsWith('//')) {
    return true;
  }
  // Absolute URLs: only allow http(s)
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}
