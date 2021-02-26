import * as React from 'react';

const TimezoneStorageKey = 'TimezonePreference';

type Value = [string, (next: string) => void];

export const TimezoneContext = React.createContext<Value>(['UTC', () => {}]);

export const TimezoneProvider: React.FC = (props) => {
  const [value, setValue] = React.useState(
    () => window.localStorage.getItem(TimezoneStorageKey) || 'Automatic',
  );

  const onChange = React.useCallback((tz: string) => {
    window.localStorage.setItem(TimezoneStorageKey, tz);
    setValue(tz);
  }, []);

  const provided: Value = React.useMemo(() => [value, onChange], [value, onChange]);

  return <TimezoneContext.Provider value={provided}>{props.children}</TimezoneContext.Provider>;
};
