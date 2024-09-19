import {useCallback, useMemo} from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

const HOUR_WINDOW_KEY = 'dagster.run-timeline-hour-window';

export type HourWindow = '1' | '6' | '12' | '24';

export const useHourWindow = (
  defaultValue: HourWindow,
  storageKey = HOUR_WINDOW_KEY,
): [HourWindow, (value: HourWindow) => void] => {
  const validate = useCallback(
    (value: string) => {
      switch (value) {
        case '1':
        case '6':
        case '12':
        case '24':
          return value;
        default:
          return defaultValue;
      }
    },
    [defaultValue],
  );

  const [hourWindow, setHourWindow] = useStateWithStorage(storageKey, validate);
  const setHourWindowWithDefault = useCallback(
    (value: HourWindow) => {
      setHourWindow(value || defaultValue);
    },
    [defaultValue, setHourWindow],
  );

  return useMemo(
    () => [hourWindow, setHourWindowWithDefault],
    [hourWindow, setHourWindowWithDefault],
  );
};
