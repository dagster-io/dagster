import {formatElapsedTimePadded} from '../time/formatElapsedTimePadded';

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

describe('formatElapsedTimePadded', () => {
  it.each([
    [0, '00:00:00'],
    [999, '00:00:00'],
    [10 * SECOND, '00:00:10'],
    [HOUR + MINUTE + SECOND, '01:01:01'],
    [100 * HOUR, '100:00:00'],
    [-5 * SECOND, '00:00:00'],
  ])('formats %i ms as %s', (ms, text) => {
    expect(formatElapsedTimePadded(ms)).toBe(text);
  });
});
