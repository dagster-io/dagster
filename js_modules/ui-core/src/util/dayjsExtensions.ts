/* eslint-disable no-restricted-imports */
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import timezone from 'dayjs/plugin/timezone';
import updateLocale from 'dayjs/plugin/updateLocale';
import utc from 'dayjs/plugin/utc';

type ThresholdUnit = 'second' | 'minute' | 'hour' | 'day' | 'month' | 'year';

const thresholds: {l: string; r?: number; d?: ThresholdUnit}[] = [
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

// Helper: returns ms until the relative time string will change for a given timestamp.
// Used for timing the next update when displaying a relative time.
//
export function getNextFromNowUpdateMs(unixSeconds: number): number {
  const now = dayjs();
  const then = dayjs(unixSeconds * 1000);

  let currentUnit: ThresholdUnit = 'second';
  let currentDiff = 0;

  // Iterate through thresholds to find which one we're currently in.
  // Then increment by one unit of the current threshold's `d`
  for (let i = 0; i < thresholds.length; i++) {
    const threshold = thresholds[i];
    if (!threshold) {
      break;
    }

    // Update current unit and diff if this threshold defines a unit
    if (threshold.d) {
      currentUnit = threshold.d;
      currentDiff = Math.abs(now.diff(then, currentUnit));
    }

    // Check if we're within this threshold's range or if it's the last one
    if (!threshold.r || currentDiff <= threshold.r) {
      // Found our current threshold. The time the UI needs to refresh next
      // is the lower of 1) the next threshold and 2) an additional unit in
      // our current threshold. Looking at both options is necessary for
      // the "90 seconds => 2 minutes" breakpoint.
      const nextThreshold = thresholds[i + 1];
      const nextUnitOfCurrentThreshold = then.add(currentDiff + 1, currentUnit);
      const firstUnitOfNextThreshold =
        nextThreshold && nextThreshold.r
          ? then.add(nextThreshold.r, nextThreshold.d || currentUnit)
          : then.add(1, 'year');

      return Math.min(
        Math.abs(nextUnitOfCurrentThreshold.diff(now, 'millisecond')),
        Math.abs(firstUnitOfNextThreshold.diff(now, 'millisecond')),
      );
    }
  }

  // Fallback to next year if no threshold matched, should not reach here
  const diffYear = Math.abs(now.diff(then, 'year'));
  const nextYear = then.add(diffYear + 1, 'year');
  return Math.abs(nextYear.diff(now, 'millisecond'));
}
