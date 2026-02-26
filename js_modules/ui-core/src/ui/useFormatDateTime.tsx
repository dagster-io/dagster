import {useCallback, useContext} from 'react';

import {TimeContext} from '../app/time/TimeContext';
import {browserTimezone} from '../app/time/browserTimezone';

/**
 * Return a date/time formatter function that takes the user's stored timezone into
 * account. Useful for rendering arbitrary non-typical date/time formats.
 *
 * @returns string
 */
export const useFormatDateTime = () => {
  const {
    timezone: [storedTimezone],
    hourCycle: [storedHourCycle],
  } = useContext(TimeContext);

  const timeZone = storedTimezone === 'Automatic' ? browserTimezone() : storedTimezone;
  const hourCycle = storedHourCycle === 'Automatic' ? undefined : storedHourCycle;

  return useCallback(
    (date: Date, options: Intl.DateTimeFormatOptions, language = navigator.language) => {
      return Intl.DateTimeFormat(language, {timeZone, hourCycle, ...options}).format(date);
    },
    [timeZone, hourCycle],
  );
};
