import {getTimeLabelStride} from '../getTimeLabelStride';

const ONE_HOUR = 60 * 60 * 1000;

const strideForTimeline = ({selectedHours, width}: {selectedHours: number; width: number}) =>
  getTimeLabelStride({
    interval: ONE_HOUR,
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
        rangeMs: [0, 4 * ONE_HOUR],
        width: 240,
      }),
    ).toBe(6);
  });

  it.each([
    {interval: 0, rangeMs: [0, ONE_HOUR] as [number, number], width: 500},
    {interval: ONE_HOUR, rangeMs: [ONE_HOUR, 0] as [number, number], width: 500},
    {interval: ONE_HOUR, rangeMs: [0, ONE_HOUR] as [number, number], width: 0},
  ])('falls back to one for invalid dimensions', (args) => {
    expect(getTimeLabelStride(args)).toBe(1);
  });
});
