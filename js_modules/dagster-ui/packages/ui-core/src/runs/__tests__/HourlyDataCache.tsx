import {HourlyDataCache, ONE_HOUR, breakIntoHourlyBuckets} from '../HourlyDataCache';

describe('HourlyDataCache', () => {
  let cache: HourlyDataCache<number>;

  beforeEach(() => {
    cache = new HourlyDataCache<number>();
  });

  describe('addToCache', () => {
    it('should add data to partial cache if within a single hour', () => {
      cache.addToCache(0, ONE_HOUR - 1, [1, 2, 3]);
      expect(cache.getDataForHour(0)).toEqual([1, 2, 3]);
    });

    it('throws if you attempt to add data spanning multiple hours to partial cache', () => {
      expect(() => {
        cache.addToCache(0, 2 * ONE_HOUR, [1, 2, 3, 4, 5, 6]);
      }).toThrow();
    });

    it('should promote complete hourly data to hourly cache', () => {
      cache.addToCache(0, ONE_HOUR - 1, Array(ONE_HOUR).fill(1));
      expect(cache.getDataForHour(0)).toEqual(Array(ONE_HOUR).fill(1));
    });
  });

  describe('getDataForHour', () => {
    it('should return empty array if no data is present', () => {
      expect(cache.getDataForHour(0)).toEqual([]);
    });

    it('should return data from hourly cache', () => {
      cache.addToCache(0, ONE_HOUR - 1, Array(ONE_HOUR).fill(1));
      expect(cache.getDataForHour(0)).toEqual(Array(ONE_HOUR).fill(1));
    });

    it('should return data from partial cache', () => {
      cache.addToCache(0, ONE_HOUR / 2, [1, 2, 3, 4, 5]);
      expect(cache.getDataForHour(0)).toEqual([1, 2, 3, 4, 5]);
    });
  });

  describe('getMissingRangeForHour', () => {
    it('should return the entire hour range if no data is present', () => {
      expect(cache.getMissingRangeForHour(0)).toEqual([[0, ONE_HOUR]]);
    });

    it('should return the missing ranges for partial data', () => {
      cache.addToCache(0, ONE_HOUR / 2, [1, 2, 3, 4, 5]);
      expect(cache.getMissingRangeForHour(0)).toEqual([[ONE_HOUR / 2, ONE_HOUR]]);
    });

    it('should return an empty array if the hour is fully cached', () => {
      cache.addToCache(0, ONE_HOUR - 1, Array(ONE_HOUR).fill(1));
      expect(cache.getMissingRangeForHour(0)).toEqual([]);
    });
  });

  describe('isRangeComplete', () => {
    it('should throw an error if the range spans multiple hours', () => {
      expect(() => cache.isRangeComplete(0, 2 * ONE_HOUR)).toThrow(
        'The input range spans multiple hours.',
      );
    });

    it('should return true if the range is completely cached in hourly cache', () => {
      cache.addToCache(0, ONE_HOUR - 1, Array(ONE_HOUR).fill(1));
      expect(cache.isRangeComplete(0, ONE_HOUR - 1)).toBe(true);
    });

    it('should return true if the range is completely cached in partial cache', () => {
      cache.addToCache(0, ONE_HOUR / 2, Array(ONE_HOUR / 2).fill(1));
      expect(cache.isRangeComplete(0, ONE_HOUR / 2)).toBe(true);
    });

    it('should return false if any part of the range is not cached', () => {
      cache.addToCache(0, ONE_HOUR / 2, Array(ONE_HOUR / 2).fill(1));
      expect(cache.isRangeComplete(0, ONE_HOUR - 1)).toBe(false);
    });
  });
});

describe('breakIntoHourlyBuckets', () => {
  it('should break the range into correct hourly buckets', () => {
    const startTime = 0;
    const endTime = 3 * ONE_HOUR + ONE_HOUR / 2;
    const buckets = breakIntoHourlyBuckets(startTime, endTime);
    expect(buckets).toEqual([
      [0, ONE_HOUR - 1],
      [ONE_HOUR, 2 * ONE_HOUR - 1],
      [2 * ONE_HOUR, 3 * ONE_HOUR - 1],
      [3 * ONE_HOUR, 3 * ONE_HOUR + ONE_HOUR / 2],
    ]);
  });

  it('should handle a range that starts and ends within the same hour', () => {
    const startTime = ONE_HOUR / 2;
    const endTime = ONE_HOUR;
    const buckets = breakIntoHourlyBuckets(startTime, endTime);
    expect(buckets).toEqual([[ONE_HOUR / 2, ONE_HOUR - 1]]);
  });

  it('should handle a range that spans multiple hours', () => {
    const startTime = ONE_HOUR / 2;
    const endTime = 2 * ONE_HOUR + ONE_HOUR / 2;
    const buckets = breakIntoHourlyBuckets(startTime, endTime);
    expect(buckets).toEqual([
      [ONE_HOUR / 2, ONE_HOUR - 1],
      [ONE_HOUR, 2 * ONE_HOUR - 1],
      [2 * ONE_HOUR, 2 * ONE_HOUR + ONE_HOUR / 2],
    ]);
  });
});
