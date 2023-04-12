import {secondsToCountdownTime} from '../secondsToCountdownTime';

describe('secondsToCountdownTime', () => {
  it('formats seconds-only', () => {
    expect(secondsToCountdownTime(0)).toBe('0:00');
    expect(secondsToCountdownTime(8)).toBe('0:08');
    expect(secondsToCountdownTime(38)).toBe('0:38');
    expect(secondsToCountdownTime(59)).toBe('0:59');
  });

  it('formats minutes and seconds', () => {
    expect(secondsToCountdownTime(60)).toBe('1:00');
    expect(secondsToCountdownTime(61)).toBe('1:01');
    expect(secondsToCountdownTime(119)).toBe('1:59');
    expect(secondsToCountdownTime(120)).toBe('2:00');
    expect(secondsToCountdownTime(121)).toBe('2:01');
    expect(secondsToCountdownTime(599)).toBe('9:59');
    expect(secondsToCountdownTime(600)).toBe('10:00');
    expect(secondsToCountdownTime(3599)).toBe('59:59');
  });

  it('formats hours, minutes, and seconds', () => {
    expect(secondsToCountdownTime(3600)).toBe('1:00:00');
    expect(secondsToCountdownTime(3601)).toBe('1:00:01');
    expect(secondsToCountdownTime(3659)).toBe('1:00:59');
    expect(secondsToCountdownTime(3660)).toBe('1:01:00');
    expect(secondsToCountdownTime(3600 + 3599)).toBe('1:59:59');
    expect(secondsToCountdownTime(3600 * 2)).toBe('2:00:00');
    expect(secondsToCountdownTime(36000 - 1)).toBe('9:59:59');
    expect(secondsToCountdownTime(36000)).toBe('10:00:00');
  });
});
