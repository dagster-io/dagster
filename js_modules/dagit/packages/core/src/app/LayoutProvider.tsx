import * as React from 'react';
import {useLocation} from 'react-router-dom';

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

export const LayoutProvider = (props: {children: React.ReactNode}) => {
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
  const isSmallScreen = useMatchMedia('(max-width: 1440px)');

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

  const [canOpen, setCanOpen] = React.useState(true);

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen: canOpen && isOpen,
        isSmallScreen,
        open,
        close,
        canOpen,
        setCanOpen,
      },
    }),
    [isOpen, isSmallScreen, open, close, canOpen, setCanOpen],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
