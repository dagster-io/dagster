import {getTimeLabelStride} from '../getTimeLabelStride';

const ONE_HOUR = 60 * 60 * 1000;
const HOURLY_LABEL_SPACING = 48;
const DAY_PERIOD_MINUTE_LABEL_SPACING = 96;

const strideForTimeline = ({selectedHours, width}: {selectedHours: number; width: number}) =>
  getTimeLabelStride({
    interval: ONE_HOUR,
    minLabelSpacing: HOURLY_LABEL_SPACING,
    rangeMs: [0, (selectedHours + 1) * ONE_HOUR],
    width,
  });

describe('getTimeLabelStride', () => {
  it.each([
    {selectedHours: 1, expectedStride: 1},
    {selectedHours: 6, expectedStride: 1},
    {selectedHours: 12, expectedStride: 2},
    {selectedHours: 24, expectedStride: 4},
  ])(
    'uses a stride of $expectedStride for a narrow $selectedHours hour timeline',
    ({selectedHours, expectedStride}) => {
      expect(strideForTimeline({selectedHours, width: 380})).toBe(expectedStride);
    },
  );

  it.each([1, 6, 12, 24])('keeps hourly labels for a wide %s hour timeline', (selectedHours) => {
    expect(strideForTimeline({selectedHours, width: 1280})).toBe(1);
  });

  it('rounds up to a readable interval', () => {
    expect(strideForTimeline({selectedHours: 24, width: 240})).toBe(6);
  });

  it('supports sub-hour intervals used by the execution timeline', () => {
    expect(
      getTimeLabelStride({
        interval: ONE_HOUR / 6,
        minLabelSpacing: DAY_PERIOD_MINUTE_LABEL_SPACING,
        rangeMs: [0, 4 * ONE_HOUR],
        width: 240,
      }),
    ).toBe(12);
  });

  it('shows more sub-hour labels when enough width is available', () => {
    expect(
      getTimeLabelStride({
        interval: ONE_HOUR / 6,
        minLabelSpacing: DAY_PERIOD_MINUTE_LABEL_SPACING,
        rangeMs: [0, 4 * ONE_HOUR],
        width: 720,
      }),
    ).toBe(4);
  });

  it('keeps every label at the exact spacing boundary', () => {
    expect(
      getTimeLabelStride({
        interval: ONE_HOUR / 6,
        minLabelSpacing: DAY_PERIOD_MINUTE_LABEL_SPACING,
        rangeMs: [0, 4 * ONE_HOUR],
        width: 24 * DAY_PERIOD_MINUTE_LABEL_SPACING,
      }),
    ).toBe(1);
  });

  it('increases the stride one pixel below the spacing boundary', () => {
    expect(
      getTimeLabelStride({
        interval: ONE_HOUR / 6,
        minLabelSpacing: DAY_PERIOD_MINUTE_LABEL_SPACING,
        rangeMs: [0, 4 * ONE_HOUR],
        width: 24 * DAY_PERIOD_MINUTE_LABEL_SPACING - 1,
      }),
    ).toBe(2);
  });

  it('returns the required stride when it exceeds the predefined nice values', () => {
    expect(
      getTimeLabelStride({
        interval: ONE_HOUR,
        minLabelSpacing: HOURLY_LABEL_SPACING,
        rangeMs: [0, 24 * ONE_HOUR],
        width: 24,
      }),
    ).toBe(48);
  });

  it.each([
    {
      interval: 0,
      minLabelSpacing: HOURLY_LABEL_SPACING,
      rangeMs: [0, ONE_HOUR] as [number, number],
      width: 500,
    },
    {
      interval: ONE_HOUR,
      minLabelSpacing: HOURLY_LABEL_SPACING,
      rangeMs: [ONE_HOUR, 0] as [number, number],
      width: 500,
    },
    {
      interval: ONE_HOUR,
      minLabelSpacing: HOURLY_LABEL_SPACING,
      rangeMs: [0, ONE_HOUR] as [number, number],
      width: 0,
    },
    {
      interval: ONE_HOUR,
      minLabelSpacing: 0,
      rangeMs: [0, ONE_HOUR] as [number, number],
      width: 500,
    },
  ])('falls back to one for invalid dimensions', (args) => {
    expect(getTimeLabelStride(args)).toBe(1);
  });
});
