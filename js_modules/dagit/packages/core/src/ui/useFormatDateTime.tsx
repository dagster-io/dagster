import * as React from 'react';

import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';

/**
 * Return a date/time formatter function that takes the user's stored timezone into
 * account. Useful for rendering arbitrary non-typical date/time formats.
 *
 * @returns string
 */
export const useFormatDateTime = () => {
  const [storedTimezone] = React.useContext(TimezoneContext);
  const timeZone = storedTimezone === 'Automatic' ? browserTimezone() : storedTimezone;
  return React.useCallback(
    (date: Date, options: Intl.DateTimeFormatOptions) => {
      return Intl.DateTimeFormat(navigator.language, {timeZone, ...options}).format(date);
    },
    [timeZone],
  );
};
