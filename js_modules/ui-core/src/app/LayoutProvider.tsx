import * as React from 'react';
import {useLocation} from 'react-router-dom';

import {isMobileDevice, useIsMobileLayout, writeViewportMetaTag} from './layout/LayoutMode';
import {useMobileRouteEnabled} from './layout/mobileRouteStatus';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

function useMatchMedia(query: string) {
  const match = React.useRef(matchMedia(query));
  const [result, setResult] = React.useState(match.current.matches);

  React.useEffect(() => {
    const matcher = match.current;
    const onChange = () => setResult(matcher.matches);
    matcher.addEventListener('change', onChange);
    return () => {
      matcher.removeEventListener('change', onChange);
    };
  }, [query]);

  return result;
}

type LayoutContextValue = {
  nav: {
    canOpen: boolean;
    isOpen: boolean;
    isSmallScreen: boolean;
    open: () => void;
    close: () => void;
    setCanOpen: (canOpen: boolean) => void;
  };
};

export const LayoutContext = React.createContext<LayoutContextValue>({
  nav: {
    canOpen: true,
    isOpen: false,
    isSmallScreen: false,
    open: () => {},
    close: () => {},
    setCanOpen: (_canOpen: boolean) => {},
  },
});

const STORAGE_KEY = 'large-screen-nav-open';

// A phone showing the desktop layout (fallback route, or the user chose desktop) gets the
// wide, zoomable viewport rather than the desktop layout crushed to device width.
const useViewportForLayout = () => {
  const isMobileRouteEnabled = useMobileRouteEnabled();
  React.useLayoutEffect(() => {
    if (isMobileDevice()) {
      writeViewportMetaTag(isMobileRouteEnabled ? 'device' : 'desktop');
    }
  }, [isMobileRouteEnabled]);
};

/**
 * Open/closed state for the navigation drawer. On small screens the drawer is transient
 * and closes on navigation; on large screens the state persists.
 */
export const LayoutProvider = (props: {children: React.ReactNode}) => {
  useViewportForLayout();

  const [navOpenIfLargeScreen, setNavOpenIfLargeScreen] = useStateWithStorage(
    STORAGE_KEY,
    (json: any) => {
      if (typeof json !== 'boolean') {
        return false;
      }
      return json;
    },
  );

  const [navOpenIfSmallScreen, setNavOpenIfSmallScreen] = React.useState(false);
  const location = useLocation();
  const isNarrowWindow = useMatchMedia('(max-width: 1440px)');
  const isMobile = useIsMobileLayout();
  const isSmallScreen = isNarrowWindow || isMobile;

  const open = React.useCallback(() => {
    setNavOpenIfSmallScreen(true);
    if (!isSmallScreen) {
      setNavOpenIfLargeScreen(true);
    }
  }, [isSmallScreen, setNavOpenIfLargeScreen]);

  const close = React.useCallback(() => {
    setNavOpenIfSmallScreen(false);
    if (!isSmallScreen) {
      setNavOpenIfLargeScreen(false);
    }
  }, [isSmallScreen, setNavOpenIfLargeScreen]);

  React.useEffect(() => {
    setNavOpenIfSmallScreen(false);
  }, [location]);

  const isOpen = isSmallScreen ? navOpenIfSmallScreen : navOpenIfLargeScreen;

  // Pages that hide the desktop nav (catalog mode, org settings) set `canOpen` false; the
  // mobile drawer is the only navigation, so it ignores that.
  const [canOpen, setCanOpen] = React.useState(true);

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen: (isMobile || canOpen) && isOpen,
        isSmallScreen,
        open,
        close,
        canOpen,
        setCanOpen,
      },
    }),
    [isOpen, isSmallScreen, isMobile, open, close, canOpen, setCanOpen],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
