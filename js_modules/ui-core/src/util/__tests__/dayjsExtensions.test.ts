import dayjs from 'dayjs';

import {getNextFromNowUpdateMs} from '../dayjsExtensions';

describe('getNextFromNowUpdateMs', () => {
  beforeEach(() => {
    // Mock the current time to ensure consistent test results
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2023-01-01T12:00:00.000Z'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('returns correct ms for seconds threshold (0-44 seconds)', () => {
    const now = dayjs();
    // 30 seconds ago
    const thirtySecondsAgo = now.subtract(30, 'second').unix();
    expect(dayjs(thirtySecondsAgo * 1000).fromNow()).toEqual('30 seconds ago');

    const result = getNextFromNowUpdateMs(thirtySecondsAgo);

    // Should update when we hit 31 seconds (next second)
    expect(result).toBe(1000);
  });

  test('returns correct ms for minute threshold (89+ seconds)', () => {
    const now = dayjs();
    // 60 seconds ago (1 minute)
    const twoMinutesAgo = now.subtract(91, 'second').unix();
    expect(dayjs(twoMinutesAgo * 1000).fromNow()).toEqual('2 minutes ago');

    const result = getNextFromNowUpdateMs(twoMinutesAgo);

    // Should update when we hit "3 minutes ago" (29 seconds from now)
    const expected = Math.abs(now.add(120 - 91, 'second').diff(now, 'millisecond'));
    expect(result).toBe(expected);
  });

  test('returns correct ms for minutes threshold (90 seconds - 44 minutes)', () => {
    const now = dayjs();
    // 5 minutes ago
    const fiveMinutesAgo = now.subtract(5, 'minute').unix();
    expect(dayjs(fiveMinutesAgo * 1000).fromNow()).toEqual('5 minutes ago');

    const result = getNextFromNowUpdateMs(fiveMinutesAgo);

    // Should update when we hit 6 minutes (1 minute from now)
    expect(result).toBe(60 * 1000);
  });

  test('returns correct ms for hour threshold (90+ minutes)', () => {
    const now = dayjs();
    // 60 minutes ago (1 hour)
    const minutesAgo = now.subtract(91, 'minute').unix();
    expect(dayjs(minutesAgo * 1000).fromNow()).toEqual('2 hours ago');

    const result = getNextFromNowUpdateMs(minutesAgo);

    // Should update when we hit 2 hours (1 hour from now)
    const expected = Math.abs(now.add(120 - 91, 'minute').diff(now, 'millisecond'));
    expect(result).toBe(expected);
  });

  test('returns correct ms for hours threshold (90 minutes - 47 hours)', () => {
    const now = dayjs();
    // 5 hours ago
    const hoursAgo = now.subtract(42, 'hour').unix();
    expect(dayjs(hoursAgo * 1000).fromNow()).toEqual('42 hours ago');

    const result = getNextFromNowUpdateMs(hoursAgo);

    // Should update when we hit the next hour (1 hour from now)
    expect(result).toBe(60 * 60 * 1000);
  });

  test('returns correct ms for days threshold (48 hours - 25 days)', () => {
    const now = dayjs();
    // 3 days ago
    const threeDaysAgo = now.subtract(3, 'day').unix();
    expect(dayjs(threeDaysAgo * 1000).fromNow()).toEqual('3 days ago');

    const result = getNextFromNowUpdateMs(threeDaysAgo);

    // Should update when we hit 4 days (1 day from now)
    expect(result).toBe(24 * 60 * 60 * 1000);
  });

  test('returns correct ms for month threshold (45 days => 2 month)', () => {
    const now = dayjs();
    // 30 days ago
    const daysAgo = now.subtract(46, 'day').unix();
    expect(dayjs(daysAgo * 1000).fromNow()).toEqual('2 months ago');

    const result = getNextFromNowUpdateMs(daysAgo);

    // Should update when we hit next month boundary
    const expected = Math.abs(now.add(61 - 46, 'day').diff(now, 'millisecond'));
    expect(result).toBe(expected);
  });

  test('returns correct ms for months threshold (<10 months)', () => {
    const now = dayjs();
    // 3 months ago
    const threeMonthsAgo = now.subtract(3, 'month').unix();
    expect(dayjs(threeMonthsAgo * 1000).fromNow()).toEqual('3 months ago');

    const result = getNextFromNowUpdateMs(threeMonthsAgo);

    // Should update when we hit 4 months (1 month from now)
    const expected = Math.abs(now.add(1, 'month').diff(now, 'millisecond'));
    expect(result).toBe(expected);
  });

  test('returns correct ms for year threshold (11-17 months)', () => {
    const now = dayjs();
    // 12 months ago (1 year)
    const oneYearAgo = now.subtract(12, 'month').unix();
    expect(dayjs(oneYearAgo * 1000).fromNow()).toEqual('a year ago');

    const result = getNextFromNowUpdateMs(oneYearAgo);

    // Should update when we hit 2 years (1 year from now)
    const expected = Math.abs(now.subtract(12, 'month').add(1, 'year').diff(now, 'millisecond'));
    expect(result).toBe(expected);
  });

  test('returns correct ms for years threshold (18+ months)', () => {
    const now = dayjs();
    // 2 years ago
    const twoYearsAgo = now.subtract(2, 'year').unix();
    expect(dayjs(twoYearsAgo * 1000).fromNow()).toEqual('2 years ago');

    const result = getNextFromNowUpdateMs(twoYearsAgo);

    // Should update when we hit 3 years (1 year from now)
    const expected = Math.abs(now.subtract(2, 'year').add(1, 'year').diff(now, 'millisecond'));
    expect(result).toBe(expected);
  });

  test('handles exact threshold boundaries', () => {
    const now = dayjs();
    // Exactly 44 seconds ago (boundary between seconds and minute)
    const exactBoundary = now.subtract(44, 'second').unix();
    expect(dayjs(exactBoundary * 1000).fromNow()).toEqual('44 seconds ago');

    const result = getNextFromNowUpdateMs(exactBoundary);

    // Should be at the seconds threshold still
    expect(result).toBe(1000);
  });

  test('handles zero timestamp (epoch)', () => {
    const result = getNextFromNowUpdateMs(0);

    // Should return a valid positive number
    expect(result).toBeGreaterThan(0);
    expect(typeof result).toBe('number');
  });

  test('handles very large timestamp', () => {
    const futureTimestamp = dayjs().add(100, 'year').unix();
    expect(dayjs(futureTimestamp * 1000).fromNow()).toEqual('in 100 years');

    const result = getNextFromNowUpdateMs(futureTimestamp);

    // Should return a valid positive number
    expect(result).toBeGreaterThan(0);
    expect(typeof result).toBe('number');
  });

  test('consistent results for same input', () => {
    const now = dayjs();
    const fiveMinutesAgo = now.subtract(5, 'minute').unix();
    expect(dayjs(fiveMinutesAgo * 1000).fromNow()).toEqual('5 minutes ago');

    const result1 = getNextFromNowUpdateMs(fiveMinutesAgo);
    const result2 = getNextFromNowUpdateMs(fiveMinutesAgo);

    expect(result1).toBe(result2);
  });

  test('returns different values as time progresses', () => {
    const now = dayjs();
    const fiveMinutesAgo = now.subtract(5, 'minute').unix();
    expect(dayjs(fiveMinutesAgo * 1000).fromNow()).toEqual('5 minutes ago');

    const result1 = getNextFromNowUpdateMs(fiveMinutesAgo);

    // Advance time by 30 seconds
    jest.advanceTimersByTime(30000);

    const result2 = getNextFromNowUpdateMs(fiveMinutesAgo);

    // Results should be different as time has progressed
    expect(result1).not.toBe(result2);
    expect(result2).toBeLessThan(result1);
  });
});
