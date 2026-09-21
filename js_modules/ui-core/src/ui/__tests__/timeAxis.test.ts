import {buildTimeAxis} from '../timeAxis';

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

// A round starting point, so a tick landing off a clock boundary is obvious in a failure.
const NOON = Date.UTC(2026, 0, 1, 12, 0, 0);

const majorTimes = (axis: ReturnType<typeof buildTimeAxis>) =>
  axis.ticks.filter((tick) => tick.isMajor).map((tick) => tick.time);

describe('buildTimeAxis', () => {
  it('labels round minutes across a few minutes of history', () => {
    const axis = buildTimeAxis({
      start: NOON + 20 * SECOND,
      end: NOON + 5 * MINUTE,
      width: 1000,
      minLabelSpacingPx: 160,
    });

    expect(axis.intervalMs).toBe(MINUTE);
    expect(majorTimes(axis)).toEqual([
      NOON + MINUTE,
      NOON + 2 * MINUTE,
      NOON + 3 * MINUTE,
      NOON + 4 * MINUTE,
      NOON + 5 * MINUTE,
    ]);
  });

  it('widens the interval as the range grows', () => {
    const overADay = buildTimeAxis({
      start: NOON,
      end: NOON + 24 * HOUR,
      width: 1000,
      minLabelSpacingPx: 160,
    });

    expect(overADay.intervalMs).toBe(6 * HOUR);
    expect(majorTimes(overADay)).toEqual([
      NOON,
      NOON + 6 * HOUR,
      NOON + 12 * HOUR,
      NOON + 18 * HOUR,
      NOON + 24 * HOUR,
    ]);
  });

  it('subdivides the major interval with rounder, sparser minor ticks', () => {
    const axis = buildTimeAxis({
      start: NOON,
      end: NOON + HOUR,
      width: 1000,
      minLabelSpacingPx: 160,
    });

    expect(axis.intervalMs).toBe(10 * MINUTE);

    // Every tick, major or not, is a whole number of minutes past the hour.
    for (const {time} of axis.ticks) {
      expect((time - NOON) % MINUTE).toBe(0);
    }

    const spacings = axis.ticks.slice(1).map((tick, i) => {
      const previous = axis.ticks[i];
      return previous ? tick.time - previous.time : 0;
    });
    expect(new Set(spacings)).toEqual(new Set([5 * MINUTE]));
  });

  it('honors a floor on the major interval', () => {
    const axis = buildTimeAxis({
      start: NOON,
      end: NOON + 5 * MINUTE,
      width: 4000,
      minLabelSpacingPx: 10,
      minIntervalMs: MINUTE,
    });

    expect(axis.intervalMs).toBe(MINUTE);
  });

  it('returns nothing for an unmeasured or empty range', () => {
    expect(
      buildTimeAxis({start: NOON, end: NOON + HOUR, width: 0, minLabelSpacingPx: 160}),
    ).toEqual({intervalMs: 0, ticks: []});
    expect(buildTimeAxis({start: NOON, end: NOON, width: 1000, minLabelSpacingPx: 160})).toEqual({
      intervalMs: 0,
      ticks: [],
    });
  });
});
