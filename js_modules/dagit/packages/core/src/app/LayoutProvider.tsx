import * as React from 'react';
import {useLocation} from 'react-router-dom';

type LayoutContextValue = {
  nav: {
    isOpen: boolean;
    open: () => void;
    close: () => void;
  };
};

export const LayoutContext = React.createContext<LayoutContextValue>({
  nav: {
    isOpen: false,
    open: () => {},
    close: () => {},
  },
});

export const LayoutProvider: React.FC = (props) => {
  const [navOpen, setNavOpen] = React.useState(true);
  const location = useLocation();

  React.useEffect(() => {
    setNavOpen(false);
  }, [location]);

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen: navOpen,
        open: () => setNavOpen(true),
        close: () => setNavOpen(false),
      },
    }),
    [navOpen],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
