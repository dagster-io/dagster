import * as React from 'react';
import {useLocation} from 'react-router-dom';

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

  React.useEffect(() => {
    setNavOpen(false);
  }, [location]);

  const value = React.useMemo(
    () => ({
      nav: {
        isOpen: navOpen,
        isCollapsible: true,
        open: () => setNavOpen(true),
        close: () => setNavOpen(false),
      },
    }),
    [navOpen],
  );

  return <LayoutContext.Provider value={value}>{props.children}</LayoutContext.Provider>;
};
