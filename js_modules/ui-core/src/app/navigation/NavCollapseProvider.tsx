import {createContext, useCallback, useContext, useMemo} from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {LayoutContext} from '../LayoutProvider';

type NavCollapseContextValue = {
  isCollapsed: boolean;
  toggleCollapsed: () => void;
};

export const NavCollapseContext = createContext<NavCollapseContextValue>({
  isCollapsed: false,
  toggleCollapsed: () => {},
});

const STORAGE_KEY = 'dagster-nav-collapsed';

export const NavCollapseProvider = (props: {children: React.ReactNode}) => {
  const [isCollapsed, setIsCollapsed] = useStateWithStorage(STORAGE_KEY, (json: any) =>
    typeof json !== 'boolean' ? false : json,
  );

  // On mobile the nav renders as an overlay drawer, which is always full width.
  const {isMobileScreen} = useContext(LayoutContext).nav;

  const toggleCollapsed = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, [setIsCollapsed]);

  const value = useMemo(
    () => ({isCollapsed: isMobileScreen ? false : isCollapsed, toggleCollapsed}),
    [isCollapsed, isMobileScreen, toggleCollapsed],
  );

  return <NavCollapseContext.Provider value={value}>{props.children}</NavCollapseContext.Provider>;
};
