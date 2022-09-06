import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

const HOUR_WINDOW_KEY = 'dagit.run-timeline-hour-window';

export type HourWindow = '1' | '6' | '12' | '24';

export const useHourWindow = (
  defaultValue: HourWindow,
): [HourWindow, (value: HourWindow) => void] => {
  const validate = React.useCallback(
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

  const [hourWindow, setHourWindow] = useStateWithStorage(HOUR_WINDOW_KEY, validate);
  const setHourWindowWithDefault = React.useCallback(
    (value: HourWindow) => {
      setHourWindow(value || defaultValue);
    },
    [defaultValue, setHourWindow],
  );

  return React.useMemo(() => [hourWindow, setHourWindowWithDefault], [
    hourWindow,
    setHourWindowWithDefault,
  ]);
};
