import * as React from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';

const TimezoneStorageKey = 'TimezonePreference';

export const TimezoneContext = React.createContext<
  [string, React.Dispatch<React.SetStateAction<string | undefined>>]
>(['UTC', () => '']);

const validateTimezone = (saved: string | undefined) =>
  typeof saved === 'string' ? saved : 'Automatic';

export const TimezoneProvider: React.FC = (props) => {
  const state = useStateWithStorage(TimezoneStorageKey, validateTimezone);

  return <TimezoneContext.Provider value={state}>{props.children}</TimezoneContext.Provider>;
};
