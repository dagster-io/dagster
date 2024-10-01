import * as React from 'react';
import {useLocation} from 'react-router-dom';

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
    open: () => void;
    close: () => void;
    setCanOpen: (canOpen: boolean) => void;
  };
};

export const LayoutContext = React.createContext<LayoutContextValue>({
  nav: {
    canOpen: true,
    isOpen: false,
    open: () => {},
    close: () => {},
    setCanOpen: (_canOpen: boolean) => {},
  },
});

export const LayoutProvider = (props: {children: React.ReactNode}) => {
  const [navOpen, setNavOpen] = React.useState(false);
  const location = useLocation();

  const open = React.useCallback(() => {
    setNavOpen(true);
  }, []);

  const close = React.useCallback(() => {
    setNavOpen(false);
  }, []);

  React.useEffect(() => {
    setNavOpen(false);
  }, [location]);

  const [canOpen, setCanOpen] = React.useState(true);

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen: canOpen && navOpen,
        open,
        close,
        canOpen,
        setCanOpen,
      },
    }),
    [canOpen, navOpen, open, close],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
