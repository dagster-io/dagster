import {PREFER_DESKTOP_SITE_STORAGE_KEY} from '../../UserSettingsDialog/usePreferDesktopSite';
import {LAYOUT_MODE_SESSION_KEY, detectLayoutMode, isMobileDevice} from '../LayoutMode';

// Written the way `useStateWithStorage` writes it.
const storePreference = (value: unknown) => {
  if (value === null) {
    window.localStorage.removeItem(PREFER_DESKTOP_SITE_STORAGE_KEY);
  } else {
    window.localStorage.setItem(PREFER_DESKTOP_SITE_STORAGE_KEY, JSON.stringify(value));
  }
};

const IPHONE_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const MAC_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';

const setDevice = ({
  userAgent,
  screenWidth,
  screenHeight = 900,
  userAgentData,
}: {
  userAgent: string;
  screenWidth: number;
  screenHeight?: number;
  userAgentData?: {mobile: boolean};
}) => {
  Object.defineProperty(window.navigator, 'userAgent', {value: userAgent, configurable: true});
  Object.defineProperty(window.navigator, 'userAgentData', {
    value: userAgentData,
    configurable: true,
  });
  Object.defineProperty(window.screen, 'width', {value: screenWidth, configurable: true});
  Object.defineProperty(window.screen, 'height', {value: screenHeight, configurable: true});
};

const setUrl = (path: string) => {
  window.history.replaceState({}, '', path);
};

describe('detectLayoutMode', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    setUrl('/runs');
  });

  it('is desktop for a desktop UA', () => {
    setDevice({userAgent: MAC_UA, screenWidth: 1440});
    expect(detectLayoutMode()).toBe('desktop');
  });

  it('is mobile for a phone UA on a small screen', () => {
    setDevice({userAgent: IPHONE_UA, screenWidth: 390, screenHeight: 844});
    expect(detectLayoutMode()).toBe('mobile');
  });

  it('is mobile for a phone held in landscape', () => {
    setDevice({userAgent: IPHONE_UA, screenWidth: 915, screenHeight: 412});
    expect(isMobileDevice()).toBe(true);
  });

  it('prefers userAgentData when present', () => {
    setDevice({userAgent: MAC_UA, screenWidth: 412, userAgentData: {mobile: true}});
    expect(isMobileDevice()).toBe(true);
    setDevice({userAgent: IPHONE_UA, screenWidth: 412, userAgentData: {mobile: false}});
    expect(isMobileDevice()).toBe(false);
  });

  it('honors "Request Desktop Site" (desktop UA on a small screen)', () => {
    setDevice({userAgent: MAC_UA, screenWidth: 390});
    expect(detectLayoutMode()).toBe('desktop');
  });

  it('honors the stored desktop-site preference', () => {
    setDevice({userAgent: IPHONE_UA, screenWidth: 390});
    storePreference(true);
    expect(detectLayoutMode()).toBe('desktop');

    storePreference(false);
    expect(detectLayoutMode()).toBe('mobile');

    storePreference(null);
    expect(detectLayoutMode()).toBe('mobile');
  });

  it('never forces the mobile layout from storage', () => {
    setDevice({userAgent: MAC_UA, screenWidth: 1440});
    storePreference('mobile');
    expect(detectLayoutMode()).toBe('desktop');
  });

  it('keeps ?layout= for the session, strips it from the URL, and prefers it over the stored preference', () => {
    setDevice({userAgent: MAC_UA, screenWidth: 1440});
    storePreference(true);
    setUrl('/runs?layout=mobile&view=all');

    expect(detectLayoutMode()).toBe('mobile');
    expect(window.location.search).toBe('?view=all');
    expect(window.sessionStorage.getItem(LAYOUT_MODE_SESSION_KEY)).toBe('mobile');
    expect(window.localStorage.getItem(PREFER_DESKTOP_SITE_STORAGE_KEY)).toBe('true');

    // Subsequent loads in the same tab keep the session override.
    expect(detectLayoutMode()).toBe('mobile');
  });

  it('ignores an invalid ?layout= value', () => {
    setDevice({userAgent: MAC_UA, screenWidth: 1440});
    setUrl('/runs?layout=tablet');
    expect(detectLayoutMode()).toBe('desktop');
    expect(window.location.search).toBe('');
    expect(window.sessionStorage.getItem(LAYOUT_MODE_SESSION_KEY)).toBeNull();
  });
});
