const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

// Past this many days a short date reads better than a day count.
const MAX_DAYS = 99;

type DateFormatOptions = {
  locale: string;
  timezone: string;
};

/** Compact elapsed text: 5s ago, 12m ago, 3h ago, 9d ago, then a bare short date. */
export const formatCompactTimeAgo = (
  nowMs: number,
  thenMs: number,
  {locale, timezone}: DateFormatOptions,
) => {
  const elapsedMs = Math.max(0, nowMs - thenMs);
  if (elapsedMs < MINUTE) {
    return `${Math.floor(elapsedMs / SECOND)}s ago`;
  }
  if (elapsedMs < HOUR) {
    return `${Math.floor(elapsedMs / MINUTE)}m ago`;
  }
  if (elapsedMs < DAY) {
    return `${Math.floor(elapsedMs / HOUR)}h ago`;
  }
  const days = Math.floor(elapsedMs / DAY);
  if (days <= MAX_DAYS) {
    return `${days}d ago`;
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

/** Milliseconds until the compact text next changes. */
export const getNextCompactTimeAgoUpdateMs = (nowMs: number, thenMs: number) => {
  const elapsedMs = Math.max(0, nowMs - thenMs);
  const unit = getCompactTimeAgoUnitMs(elapsedMs);
  return unit - (elapsedMs % unit);
};
