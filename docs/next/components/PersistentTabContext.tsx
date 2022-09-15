import React from 'react';

export const PersistentTabContext = React.createContext<{
  getTabState: (string) => number;
  setTabState: (string, number) => void;
}>({getTabState: () => 0, setTabState: () => {}});

export const PersistentTabProvider: React.FC = ({children}) => {
  const [tabState, setTabState] = React.useState<{[key: string]: number}>({});

  const windowExists = typeof window !== 'undefined';
  React.useEffect(() => {
    console.log(windowExists);
    if (windowExists) {
      const ts = localStorage.getItem('persistentTabStates');
      if (ts) {
        setTabState(JSON.parse(ts));
      }
    }
  }, [setTabState, windowExists]);

  const setTabStateAndPersist = (key: string, value: number) => {
    const newTabState = {...tabState, [key]: value};
    setTabState(newTabState);
    if (typeof window !== 'undefined') {
      localStorage.setItem('persistentTabStates', JSON.stringify(newTabState));
    }
  };

  return (
    <PersistentTabContext.Provider
      value={{
        getTabState: (key: string) => tabState[key] || 0,
        setTabState: setTabStateAndPersist,
      }}
    >
      {children}
    </PersistentTabContext.Provider>
  );
};
