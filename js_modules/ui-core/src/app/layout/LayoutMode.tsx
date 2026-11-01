import {createContext, useContext} from 'react';

import {getJSONForKey} from '../../util/getJSONForKey';
import {
  PREFER_DESKTOP_SITE_STORAGE_KEY,
  validatePreferDesktopSite,
} from '../UserSettingsDialog/usePreferDesktopSite';

export type LayoutMode = 'desktop' | 'mobile';

// Per-tab override from `?layout=`, for development and previews.
export const LAYOUT_MODE_SESSION_KEY = 'dagster-layout-mode-session';
export const LAYOUT_MODE_QUERY_PARAM = 'layout';
export const MOBILE_BODY_CLASS = 'dagster-mobile';

// Phones and small tablets. iPads report a desktop UA by default and stay on desktop.
const MOBILE_SCREEN_WIDTH_MAX = 820;

export const validateLayoutMode = (value: unknown): LayoutMode | null =>
  value === 'desktop' || value === 'mobile' ? value : null;

// Session storage isn't covered by `useStateWithStorage`, and this is read before React mounts.
const readSessionLayoutMode = () => {
  try {
    return validateLayoutMode(window.sessionStorage.getItem(LAYOUT_MODE_SESSION_KEY));
  } catch {
    return null;
  }
};

const writeSessionLayoutMode = (mode: LayoutMode) => {
  try {
    window.sessionStorage.setItem(LAYOUT_MODE_SESSION_KEY, mode);
  } catch {
    // Storage may be unavailable (private mode, blocked). The override is a convenience.
  }
};

// Wide enough for the desktop layout; the browser then lets the user pinch-zoom, which is
// what "Request Desktop Site" produces natively.
const DESKTOP_VIEWPORT = 'width=1280';
const DEVICE_VIEWPORT = 'width=device-width, initial-scale=1, shrink-to-fit=no';

export const writeViewportMetaTag = (kind: 'device' | 'desktop') => {
  const meta = document.querySelector<HTMLMetaElement>('meta[name="viewport"]');
  if (meta) {
    meta.content = kind === 'desktop' ? DESKTOP_VIEWPORT : DEVICE_VIEWPORT;
  }
};

const isMobileUserAgent = () => {
  const uaData = (navigator as {userAgentData?: {mobile?: boolean}}).userAgentData;
  if (typeof uaData?.mobile === 'boolean') {
    return uaData.mobile;
  }
  return /Mobi|Android|iPhone|iPod/i.test(navigator.userAgent);
};

/**
 * Whether this looks like a phone. Deliberately not a media query:
 *
 * - "Request Desktop Site" in iOS Safari and Chrome for Android switches to a desktop UA,
 *   so a UA-based check honors it with no extra work.
 * - A narrow desktop window never becomes the mobile app.
 */
export const isMobileDevice = () => {
  if (typeof window === 'undefined') {
    return false;
  }
  // Android swaps `screen.width`/`height` with orientation; the short edge is stable.
  const shortEdge = Math.min(window.screen.width, window.screen.height);
  return isMobileUserAgent() && shortEdge > 0 && shortEdge <= MOBILE_SCREEN_WIDTH_MAX;
};

// Move a `?layout=` param into session storage and strip it from the URL so it never
// travels in a shared link.
const consumeLayoutQueryParam = () => {
  const url = new URL(window.location.href);
  const value = url.searchParams.get(LAYOUT_MODE_QUERY_PARAM);
  if (value === null) {
    return;
  }
  url.searchParams.delete(LAYOUT_MODE_QUERY_PARAM);
  window.history.replaceState(window.history.state, '', url.toString());
  const mode = validateLayoutMode(value);
  if (mode) {
    writeSessionLayoutMode(mode);
  }
};

/**
 * Decide the layout mode once, at boot: `?layout=` (kept for this tab) → the "always use the
 * desktop site" user setting → device detection. Only the desktop direction is a setting, so
 * a phone user can't get stuck in the mobile layout with the control to leave it hidden.
 */
export const detectLayoutMode = (): LayoutMode => {
  if (typeof window === 'undefined') {
    return 'desktop';
  }
  consumeLayoutQueryParam();
  return (
    readSessionLayoutMode() ??
    (validatePreferDesktopSite(getJSONForKey(PREFER_DESKTOP_SITE_STORAGE_KEY))
      ? 'desktop'
      : null) ??
    (isMobileDevice() ? 'mobile' : 'desktop')
  );
};

export const LayoutModeContext = createContext<LayoutMode>('desktop');

export const useLayoutMode = () => useContext(LayoutModeContext);
export const useIsMobileLayout = () => useLayoutMode() === 'mobile';
