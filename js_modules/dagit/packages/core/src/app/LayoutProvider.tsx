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
    isOpen: boolean;
    isSmallScreen: boolean;
    open: () => void;
    close: () => void;
  };
};

export const LayoutContext = React.createContext<LayoutContextValue>({
  nav: {
    isOpen: false,
    isSmallScreen: false,
    open: () => {},
    close: () => {},
  },
});

const STORAGE_KEY = 'large-screen-nav-open';

export const LayoutProvider: React.FC = (props) => {
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

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen,
        isSmallScreen,
        open,
        close,
      },
    }),
    [isOpen, isSmallScreen, open, close],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
