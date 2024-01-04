import memoize from 'lodash/memoize';

import {HourCycle} from './HourCycle';
import {TimeFormat, DEFAULT_TIME_FORMAT} from './TimestampFormat';
import {browserTimezone} from './browserTimezone';

type Config = {
  timestamp: {ms: number} | {unix: number};
  locale: string;
  timezone: string;
  timeFormat?: TimeFormat;
  hourCycle?: HourCycle;
};

const configWithDefaults = (config: Config) => {
  const {timeFormat = DEFAULT_TIME_FORMAT, hourCycle = 'Automatic', ...rest} = config;
  return {
    ...rest,
    timeFormat,
    hourCycle,
  };
};

// Formatting date strings can be a bit slow, and it adds up when a page has tons of timestamps.
export const resolveTimestampKey = (config: Config) => {
  const {timestamp, locale, timezone, timeFormat, hourCycle} = configWithDefaults(config);
  const msec = 'ms' in timestamp ? timestamp.ms : timestamp.unix * 1000;
  return [msec, locale, timezone, JSON.stringify(timeFormat), hourCycle].join('-');
};

export const timestampToString = memoize((config: Config) => {
  const {timestamp, locale, timezone, timeFormat, hourCycle} = configWithDefaults(config);
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
    hourCycle: hourCycle === 'Automatic' ? undefined : hourCycle,
    timeZone: targetTimezone,
    timeZoneName: timeFormat.showTimezone ? 'short' : undefined,
  });
}, resolveTimestampKey);
