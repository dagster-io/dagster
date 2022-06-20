import memoize from 'lodash/memoize';
import moment from 'moment-timezone';

import {TimeFormat, DEFAULT_TIME_FORMAT} from './TimestampFormat';
import {browserTimezone} from './browserTimezone';

type Config = {
  timestamp: {ms: number} | {unix: number};
  locale: string;
  timezone: string;
  timeFormat?: TimeFormat;
};

// This helper is here so that we can swap out Moment in the future as needed and
// encourage use of the same default format string across the app.
export const timestampToString = (config: Config) => {
  const {timestamp, locale, timezone, timeFormat = DEFAULT_TIME_FORMAT} = config;
  const m = 'ms' in timestamp ? moment(timestamp.ms) : moment.unix(timestamp.unix);
  const targetTimezone = timezone === 'Automatic' ? browserTimezone() : timezone;
  const sameYear = moment(Date.now()).tz(targetTimezone).year() === m.tz(targetTimezone).year();

  return m.toDate().toLocaleDateString(locale, {
    month: 'short',
    day: 'numeric',
    year: sameYear ? undefined : 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: timeFormat.showSeconds ? 'numeric' : undefined,
    timeZone: targetTimezone,
    timeZoneName: timeFormat.showTimezone ? 'short' : undefined,
  });
};

export const timeZoneAbbr = memoize((tzIn: string) => moment().tz(tzIn).zoneAbbr());
