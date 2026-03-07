import {createContext, useCallback, useMemo} from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';

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

  const toggleCollapsed = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, [setIsCollapsed]);

  const value = useMemo(() => ({isCollapsed, toggleCollapsed}), [isCollapsed, toggleCollapsed]);

  return <NavCollapseContext.Provider value={value}>{props.children}</NavCollapseContext.Provider>;
};
