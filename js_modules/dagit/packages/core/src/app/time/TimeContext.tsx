import * as React from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';

import {HourCycle} from './HourCycle';

export const TimezoneStorageKey = 'TimezonePreference';
export const HourCycleKey = 'HourCyclePreference';

type TimeContextValue = {
  timezone: [string, React.Dispatch<React.SetStateAction<string | undefined>>];
  hourCycle: [HourCycle, React.Dispatch<React.SetStateAction<HourCycle | undefined>>];
};

export const TimeContext = React.createContext<TimeContextValue>({
  timezone: ['UTC', () => 'UTC'],
  hourCycle: ['Automatic', () => 'Automatic'],
});

const validateTimezone = (saved: string | undefined) =>
  typeof saved === 'string' ? saved : 'Automatic';

const validateHourCycle = (saved: string | undefined) => {
  if (saved === 'h12' || saved === 'h23') {
    return saved;
  }
  return 'Automatic';
};

export const TimeProvider = (props: {children: React.ReactNode}) => {
  const timezone = useStateWithStorage(TimezoneStorageKey, validateTimezone);
  const hourCycle = useStateWithStorage(HourCycleKey, validateHourCycle);
  const state = React.useMemo(
    () => ({
      timezone,
      hourCycle,
    }),
    [timezone, hourCycle],
  );

  return <TimeContext.Provider value={state}>{props.children}</TimeContext.Provider>;
};
