import * as React from 'react';

import {HourCycle} from './HourCycle';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';

export const TimezoneStorageKey = 'TimezonePreference';
export const HourCycleKey = 'HourCyclePreference';

export type TimeContextValue = {
  timezone: ReturnType<typeof useStateWithStorage<string>>;
  hourCycle: ReturnType<typeof useStateWithStorage<HourCycle>>;
};

export const TimeContext = React.createContext<TimeContextValue>({
  timezone: ['UTC', () => 'UTC', () => {}],
  hourCycle: ['Automatic', () => 'Automatic', () => {}],
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
