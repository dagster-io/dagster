import {unitToShortLabel} from '../../ui/formatDuration';

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

// Past this many days a short date reads better than a day count.
const MAX_DAYS = 99;

type ShortLabelUnit = keyof typeof unitToShortLabel;

const formatUnitsAgo = (count: number, singular: ShortLabelUnit, plural: ShortLabelUnit) =>
  `${count} ${unitToShortLabel[count === 1 ? singular : plural]} ago`;

type DateFormatOptions = {
  locale: string;
  timezone: string;
};

/** Compact elapsed text: 5 sec ago, 12 min ago, 3 hr ago, 9 days ago, then a bare short date. */
export const formatCompactTimeAgo = (
  nowMs: number,
  thenMs: number,
  {locale, timezone}: DateFormatOptions,
) => {
  const elapsedMs = Math.max(0, nowMs - thenMs);
  if (elapsedMs < MINUTE) {
    return formatUnitsAgo(Math.floor(elapsedMs / SECOND), 'second', 'seconds');
  }
  if (elapsedMs < HOUR) {
    return formatUnitsAgo(Math.floor(elapsedMs / MINUTE), 'minute', 'minutes');
  }
  if (elapsedMs < DAY) {
    return formatUnitsAgo(Math.floor(elapsedMs / HOUR), 'hour', 'hours');
  }
  const days = Math.floor(elapsedMs / DAY);
  if (days <= MAX_DAYS) {
    return formatUnitsAgo(days, 'day', 'days');
  }

  // Any fixed locale serves the comparison; the displayed date uses the caller's locale.
  const yearOf = (ms: number) =>
    new Date(ms).toLocaleDateString('en-US', {year: 'numeric', timeZone: timezone});

  return new Date(thenMs).toLocaleDateString(locale, {
    month: 'short',
    day: 'numeric',
    year: yearOf(thenMs) === yearOf(nowMs) ? undefined : 'numeric',
    timeZone: timezone,
  });
};

const getCompactTimeAgoUnitMs = (elapsedMs: number) => {
  if (elapsedMs < MINUTE) {
    return SECOND;
  }
  if (elapsedMs < HOUR) {
    return MINUTE;
  }
  if (elapsedMs < DAY) {
    return HOUR;
  }
  return DAY;
};

export const getNextCompactTimeAgoUpdateMs = (nowMs: number, thenMs: number) => {
  const elapsedMs = Math.max(0, nowMs - thenMs);
  const unit = getCompactTimeAgoUnitMs(elapsedMs);
  return unit - (elapsedMs % unit);
};
