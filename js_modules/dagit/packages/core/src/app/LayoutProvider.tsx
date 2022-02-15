import * as React from 'react';
import {useLocation} from 'react-router-dom';

import {useFeatureFlags} from './Flags';

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
    isCollapsible: boolean;
    open: () => void;
    close: () => void;
  };
};

export const LayoutContext = React.createContext<LayoutContextValue>({
  nav: {
    isOpen: false,
    isCollapsible: false,
    open: () => {},
    close: () => {},
  },
});

export const LayoutProvider: React.FC = (props) => {
  const [navOpen, setNavOpen] = React.useState(false);
  const location = useLocation();
  const isSmallScreen = useMatchMedia('(max-width: 1440px)');
  const isInstancePage = location.pathname.startsWith('/instance');

  React.useEffect(() => {
    setNavOpen(false);
  }, [location]);

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen: navOpen,
        isCollapsible: isInstancePage || isSmallScreen,
        open: () => setNavOpen(true),
        close: () => setNavOpen(false),
      },
    }),
    [navOpen, isInstancePage, isSmallScreen],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
