/* eslint-disable no-restricted-imports */
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import timezone from 'dayjs/plugin/timezone';
import updateLocale from 'dayjs/plugin/updateLocale';
import utc from 'dayjs/plugin/utc';

const thresholds = [
  // Read as: "Format string to use when the diff (in seconds) <= r (44)"
  // Followed by other format strings using the same diff until the next d:.
  {l: 's', r: 44, d: 'second'},
  {l: 'm', r: 89},
  {l: 'mm', r: 44, d: 'minute'},
  {l: 'h', r: 89},
  {l: 'hh', r: 47, d: 'hour'}, // We have changed this from 21 to 47
  //   {l: 'd', r: 35},           // We never show "A day ago"
  {l: 'dd', r: 25, d: 'day'},
  {l: 'M', r: 45},
  {l: 'MM', r: 10, d: 'month'},
  {l: 'y', r: 17},
  {l: 'yy', d: 'year'},
];

dayjs.extend(duration);
dayjs.extend(updateLocale);
dayjs.extend(relativeTime, {thresholds});
dayjs.extend(utc);
dayjs.extend(timezone);

dayjs.updateLocale('en', {
  relativeTime: {
    future: 'in %s',
    past: '%s ago',
    s: '%d seconds',
    m: 'a minute',
    mm: '%d minutes',
    h: 'an hour',
    hh: '%d hours',
    d: 'a day',
    dd: '%d days',
    M: 'a month',
    MM: '%d months',
    y: 'a year',
    yy: '%d years',
  },
});

// Helper: returns ms until the next fromNow breakpoint for a given timestamp
// This must be kept in sync with the DayJS configuration above.
//
export function getNextFromNowUpdateMs(unixTimestamp: number): number {
  const now = dayjs();
  const then = dayjs(unixTimestamp * 1000);
  const diffSec = Math.abs(now.diff(then, 'second'));
  const diffMin = Math.abs(now.diff(then, 'minute'));
  const diffHour = Math.abs(now.diff(then, 'hour'));
  const diffDay = Math.abs(now.diff(then, 'day'));
  const diffMonth = Math.abs(now.diff(then, 'month'));
  const diffYear = Math.abs(now.diff(then, 'year'));

  // See: https://day.js.org/docs/en/display/from-now#list-of-breakdown-range
  if (diffSec <= 44) {
    // Next change at 45s
    return (45 - diffSec) * 1000;
  } else if (diffSec <= 89) {
    // Next change at 90s
    return (90 - diffSec) * 1000;
  } else if (diffMin <= 44) {
    // Next change at next minute
    const nextMin = then.add(diffMin + 1, 'minute');
    return Math.abs(nextMin.diff(now, 'millisecond'));
  } else if (diffMin <= 89) {
    // Next change at 90min
    return (90 * 60 - diffSec) * 1000;
  } else if (diffHour <= 47) {
    // Next change at next hour
    const nextHour = then.add(diffHour + 1, 'hour');
    return Math.abs(nextHour.diff(now, 'millisecond'));
  } else if (diffDay <= 25) {
    // Next change at next day
    const nextDay = then.add(diffDay + 1, 'day');
    return Math.abs(nextDay.diff(now, 'millisecond'));
  } else if (diffDay <= 45) {
    // Next change at 46d
    return (46 * 24 * 60 * 60 - diffSec) * 1000;
  } else if (diffMonth <= 10) {
    // Next change at next month
    const nextMonth = then.add(diffMonth + 1, 'month');
    return Math.abs(nextMonth.diff(now, 'millisecond'));
  } else if (diffMonth <= 17) {
    // Next change at 1.5y (18 months)
    const nextYear = then.add(1.5, 'year');
    return Math.abs(nextYear.diff(now, 'millisecond'));
  } else {
    // Next change at next year
    const nextYear = then.add(diffYear + 1, 'year');
    return Math.abs(nextYear.diff(now, 'millisecond'));
  }
}
