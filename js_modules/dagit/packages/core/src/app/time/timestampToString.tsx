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
  const msec = 'ms' in timestamp ? timestamp.ms : timestamp.unix * 1000;
  const date = new Date(msec);
  const targetTimezone = timezone === 'Automatic' ? browserTimezone() : timezone;

  const timestampYear = date.toLocaleDateString('en-US', {
    year: 'numeric',
    timeZone: targetTimezone,
  });
  const viewerYear = new Date(Date.now()).toLocaleDateString('en-US', {
    year: 'numeric',
    timeZone: targetTimezone,
  });
  const sameYear = timestampYear === viewerYear;

  return date.toLocaleDateString(locale, {
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
