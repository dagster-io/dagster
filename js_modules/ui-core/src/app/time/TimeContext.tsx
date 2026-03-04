import * as React from 'react';

import {HourCycle} from './HourCycle';
import {browserTimezone} from './browserTimezone';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';

export const TimezoneStorageKey = 'TimezonePreference';
export const HourCycleKey = 'HourCyclePreference';

export type TimeContextValue = {
  timezone: ReturnType<typeof useStateWithStorage<string>>;
  resolvedTimezone: string;
  hourCycle: ReturnType<typeof useStateWithStorage<HourCycle>>;
};

export const TimeContext = React.createContext<TimeContextValue>({
  timezone: ['UTC', () => 'UTC', () => {}],
  resolvedTimezone: 'UTC',
  hourCycle: ['Automatic', () => 'Automatic', () => {}],
});

const validateTimezone = (saved: string | undefined) => {
  if (typeof saved === 'string' && saved !== 'Automatic') {
    return saved;
  }
  return 'LOCAL_TIMEZONE';
};

const validateHourCycle = (saved: string | undefined) => {
  if (saved === 'h12' || saved === 'h23') {
    return saved;
  }
  return 'Automatic';
};

const resolveTimezone = (preference: string): string => {
  if (
    preference === 'LOCAL_TIMEZONE' ||
    preference === 'ORG_TIMEZONE' ||
    preference === 'Automatic'
  ) {
    return browserTimezone();
  }
  return preference;
};

export const TimeProvider = (props: {children: React.ReactNode}) => {
  const timezone = useStateWithStorage(TimezoneStorageKey, validateTimezone);
  const hourCycle = useStateWithStorage(HourCycleKey, validateHourCycle);
  const resolvedTimezone = resolveTimezone(timezone[0]);
  const state = React.useMemo(
    () => ({
      timezone,
      resolvedTimezone,
      hourCycle,
    }),
    [timezone, resolvedTimezone, hourCycle],
  );

  return <TimeContext.Provider value={state}>{props.children}</TimeContext.Provider>;
};
