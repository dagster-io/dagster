import {clipEventsToSharedMinimumTime} from '../clipEventsToSharedMinimumTime';

const SHORT_TIMESPAN = [
  {timestamp: `${new Date('2024-01-01').getTime()}`},
  {timestamp: `${new Date('2024-01-02').getTime()}`},
  {timestamp: `${new Date('2024-01-03').getTime()}`},
  {timestamp: `${new Date('2024-01-04').getTime()}`},
  {timestamp: `${new Date('2024-01-05').getTime()}`},
  {timestamp: `${new Date('2024-01-06').getTime()}`},
  {timestamp: `${new Date('2024-01-07').getTime()}`},
  {timestamp: `${new Date('2024-01-08').getTime()}`},
  {timestamp: `${new Date('2024-01-09').getTime()}`},
  {timestamp: `${new Date('2024-01-10').getTime()}`},
];

const LONG_TIMESPAN = [
  {timestamp: `${new Date('2023-11-10').getTime()}`},
  {timestamp: `${new Date('2023-11-17').getTime()}`},
  {timestamp: `${new Date('2023-11-23').getTime()}`},
  {timestamp: `${new Date('2023-11-30').getTime()}`},
  {timestamp: `${new Date('2023-12-06').getTime()}`},
  {timestamp: `${new Date('2023-12-13').getTime()}`},
  {timestamp: `${new Date('2023-12-20').getTime()}`},
  {timestamp: `${new Date('2023-12-27').getTime()}`},
  {timestamp: `${new Date('2024-01-03').getTime()}`},
  {timestamp: `${new Date('2024-01-10').getTime()}`},
];

describe('clipEventsToSharedMinimumTime', () => {
  it('should clip to the minimum time in both datasets', () => {
    const {materializations, observations} = clipEventsToSharedMinimumTime(
      SHORT_TIMESPAN,
      LONG_TIMESPAN,
      10,
    );
    expect(materializations.length).toEqual(10);
    expect(observations.length).toEqual(2);
  });

  it('should clip to the minimum time in both datasets, even if the longer tiemspan dataset has <limit rows', () => {
    const {materializations, observations} = clipEventsToSharedMinimumTime(
      SHORT_TIMESPAN,
      LONG_TIMESPAN.slice(2),
      10,
    );
    expect(materializations.length).toEqual(10);
    expect(observations.length).toEqual(2);
  });

  it('should not clip if the dataset shorter timespan dataset has <limit rows', () => {
    const {materializations, observations} = clipEventsToSharedMinimumTime(
      SHORT_TIMESPAN.slice(2),
      LONG_TIMESPAN,
      10,
    );
    expect(materializations.length).toEqual(8);
    expect(observations.length).toEqual(10);
  });

  it('should not clip if both datasets returned <limit rows', () => {
    const {materializations, observations} = clipEventsToSharedMinimumTime(
      SHORT_TIMESPAN.slice(2),
      LONG_TIMESPAN.slice(2),
      10,
    );
    expect(materializations.length).toEqual(8);
    expect(observations.length).toEqual(8);
  });
});
