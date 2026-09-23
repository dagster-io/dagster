import {formatCompactTimeAgo, getNextCompactTimeAgoUpdateMs} from '../time/formatCompactTimeAgo';

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

const NOW_MS = Date.UTC(2026, 8, 16, 12, 0, 0);
const FORMAT = {locale: 'en-US', timezone: 'UTC'};

describe('formatCompactTimeAgo', () => {
  it.each([
    [0, '0s ago'],
    [59 * SECOND, '59s ago'],
    [MINUTE, '1m ago'],
    [59 * MINUTE + 59 * SECOND, '59m ago'],
    [HOUR, '1h ago'],
    [23 * HOUR, '23h ago'],
    [DAY, '1d ago'],
    [99 * DAY, '99d ago'],
  ])('formats %i ms elapsed as %s', (elapsedMs, text) => {
    expect(formatCompactTimeAgo(NOW_MS, NOW_MS - elapsedMs, FORMAT)).toBe(text);
  });

  it('treats a future timestamp as now', () => {
    expect(formatCompactTimeAgo(NOW_MS, NOW_MS + MINUTE, FORMAT)).toBe('0s ago');
  });

  it('falls back to a bare short date past 99 days', () => {
    expect(formatCompactTimeAgo(NOW_MS, Date.UTC(2026, 4, 1), FORMAT)).toBe('May 1');
  });

  it('adds the year to a date from another year', () => {
    expect(formatCompactTimeAgo(NOW_MS, Date.UTC(2025, 4, 1), FORMAT)).toBe('May 1, 2025');
  });

  it('resolves the date in the given timezone', () => {
    const lateOnMay1Utc = Date.UTC(2026, 4, 1, 23, 30);
    expect(formatCompactTimeAgo(NOW_MS, lateOnMay1Utc, {...FORMAT, timezone: 'Asia/Tokyo'})).toBe(
      'May 2',
    );
  });
});

describe('getNextCompactTimeAgoUpdateMs', () => {
  it.each([
    ['seconds', 10 * SECOND + 250, 750],
    ['minutes', 10 * MINUTE + 250, MINUTE - 250],
    ['hours', 3 * HOUR + 250, HOUR - 250],
    ['days', 5 * DAY + 250, DAY - 250],
    ['a unit boundary', MINUTE, MINUTE],
  ])('waits for the next boundary while counting %s', (_unit, elapsedMs, expected) => {
    expect(getNextCompactTimeAgoUpdateMs(NOW_MS, NOW_MS - elapsedMs)).toBe(expected);
  });
});
