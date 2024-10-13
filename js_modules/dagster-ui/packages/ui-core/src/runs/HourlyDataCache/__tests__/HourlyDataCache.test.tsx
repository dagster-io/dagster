import {HourlyDataCache, ONE_HOUR_S, getHourlyBuckets} from '../HourlyDataCache';

const mockedCache = {
  has: jest.fn(),
  get: jest.fn(),
  set: jest.fn(),
};
let mockShouldThrowError = false;
jest.mock('idb-lru-cache', () => {
  return {
    cache: jest.fn(() => {
      if (mockShouldThrowError) {
        throw new Error('Internal error opening backing store for indexedDB.open.');
      }
      return mockedCache;
    }),
  };
});
const VERSION = 1;

describe('HourlyDataCache', () => {
  let cache: HourlyDataCache<number>;

  beforeEach(() => {
    cache = new HourlyDataCache<number>({id: 'test', version: VERSION});
  });

  describe('addData', () => {
    it('should return added data', () => {
      cache.addData(0, ONE_HOUR_S, [1, 2, 3]);
      expect(cache.getHourData(0)).toEqual([1, 2, 3]);
    });

    it('throws if you attempt to add data spanning multiple hours to partial cache', () => {
      expect(() => {
        cache.addData(0, 2 * ONE_HOUR_S, [1, 2, 3, 4, 5, 6]);
      }).toThrow('Expected all data to fit within an hour');
    });
  });

  describe('getHourData', () => {
    it('should return empty array if no data is present', () => {
      expect(cache.getHourData(0)).toEqual([]);
    });

    it('should return data from hourly cache', () => {
      cache.addData(0, ONE_HOUR_S, [1]);
      expect(cache.getHourData(0)).toEqual([1]);
    });

    it('should return data from partial cache', () => {
      cache.addData(0, ONE_HOUR_S / 2, [1, 2, 3, 4, 5]);
      expect(cache.getHourData(0)).toEqual([1, 2, 3, 4, 5]);
    });
  });

  describe('getMissingIntervals', () => {
    it('should return the entire hour range if no data is present', () => {
      expect(cache.getMissingIntervals(0)).toEqual([[0, ONE_HOUR_S]]);
    });

    it('should return the missing ranges for partial data', () => {
      cache.addData(0, ONE_HOUR_S / 2, [1, 2, 3, 4, 5]);
      expect(cache.getMissingIntervals(0)).toEqual([[ONE_HOUR_S / 2, ONE_HOUR_S]]);
    });

    it('should return an empty array if the hour is fully cached', () => {
      cache.addData(0, ONE_HOUR_S, [1]);
      expect(cache.getMissingIntervals(0)).toEqual([]);
    });
  });

  describe('isCompleteRange', () => {
    it('should throw an error if the range spans multiple hours', () => {
      expect(() => cache.isCompleteRange(0, 2 * ONE_HOUR_S)).toThrow(
        'Expected the input range to be within a single hour',
      );
    });

    it('should return true if the range is completely cached in hourly cache', () => {
      cache.addData(0, ONE_HOUR_S, [1]);
      expect(cache.isCompleteRange(0, ONE_HOUR_S)).toBe(true);
    });

    it('should return true if the range is completely cached in partial cache', () => {
      cache.addData(0, ONE_HOUR_S / 2, [1]);
      expect(cache.isCompleteRange(0, ONE_HOUR_S / 2)).toBe(true);
    });

    it('should return false if any part of the range is not cached', () => {
      cache.addData(0, ONE_HOUR_S / 2, [1]);
      expect(cache.isCompleteRange(0, ONE_HOUR_S)).toBe(false);
    });
  });
});

describe('getHourlyBuckets', () => {
  it('should break the range into correct hourly buckets', () => {
    const startTime = 0;
    const endTime = 3 * ONE_HOUR_S + ONE_HOUR_S / 2;
    const buckets = getHourlyBuckets(startTime, endTime);
    expect(buckets).toEqual([
      [0, ONE_HOUR_S],
      [ONE_HOUR_S, 2 * ONE_HOUR_S],
      [2 * ONE_HOUR_S, 3 * ONE_HOUR_S],
      [3 * ONE_HOUR_S, 3 * ONE_HOUR_S + ONE_HOUR_S / 2],
    ]);
  });

  it('should handle a range that starts and ends within the same hour', () => {
    const startTime = ONE_HOUR_S / 2;
    const endTime = ONE_HOUR_S;
    const buckets = getHourlyBuckets(startTime, endTime);
    expect(buckets).toEqual([[ONE_HOUR_S / 2, ONE_HOUR_S]]);
  });

  it('should handle a range that spans multiple hours', () => {
    const startTime = ONE_HOUR_S / 2;
    const endTime = 2 * ONE_HOUR_S + ONE_HOUR_S / 2;
    const buckets = getHourlyBuckets(startTime, endTime);
    expect(buckets).toEqual([
      [ONE_HOUR_S / 2, ONE_HOUR_S],
      [ONE_HOUR_S, 2 * ONE_HOUR_S],
      [2 * ONE_HOUR_S, 2 * ONE_HOUR_S + ONE_HOUR_S / 2],
    ]);
  });
});

describe('HourlyDataCache Subscriptions', () => {
  let cache: HourlyDataCache<number>;

  beforeEach(() => {
    cache = new HourlyDataCache<number>({version: VERSION});
  });

  [true, false].forEach((shouldThrowError) => {
    const throwingError = shouldThrowError;
    describe(
      // eslint-disable-next-line jest/valid-title
      throwingError ? 'with crashing indexeddb cache' : 'with working indexeddb cache',
      () => {
        beforeEach(() => {
          mockShouldThrowError = throwingError;
          cache = new HourlyDataCache<number>({version: VERSION, id: 'test'});
        });
        it('should notify subscriber immediately with existing data', () => {
          cache.addData(0, ONE_HOUR_S, [1, 2, 3]);

          const callback = jest.fn();
          cache.subscribe(1, callback);

          expect(callback).toHaveBeenCalledWith([1, 2, 3]);
        });

        it('should notify subscriber with new data added to the subscribed hour', () => {
          const callback = jest.fn();
          cache.subscribe(0, callback);

          cache.addData(0, ONE_HOUR_S, [1, 2, 3]);

          expect(callback).toHaveBeenCalledWith([1, 2, 3]);
        });

        it('should notify subscriber with new data added to subsequent hours', () => {
          const callback = jest.fn();
          cache.subscribe(0, callback);

          cache.addData(ONE_HOUR_S, 2 * ONE_HOUR_S, [4, 5, 6]);

          expect(callback).toHaveBeenCalledWith([4, 5, 6]);
        });

        it('should aggregate data from multiple hours for the subscriber', () => {
          cache.addData(0, ONE_HOUR_S, [1, 2, 3]);

          const callback = jest.fn();
          cache.subscribe(0, callback);

          expect(callback).toHaveBeenCalledWith([1, 2, 3]);

          cache.addData(ONE_HOUR_S, 2 * ONE_HOUR_S, [4, 5, 6]);

          expect(callback).toHaveBeenCalledWith([1, 2, 3, 4, 5, 6]);
        });

        it('should not notify subscribers of data added before their subscription hour', () => {
          cache.addData(0, ONE_HOUR_S, [1, 2, 3]);

          const callback = jest.fn();
          cache.subscribe(ONE_HOUR_S, callback);

          cache.addData(2 * ONE_HOUR_S, 3 * ONE_HOUR_S, [4, 5, 6]);

          expect(callback).toHaveBeenCalledWith([4, 5, 6]);
        });

        it('should stop notifying unsubscribed callbacks', () => {
          const callback = jest.fn();
          const unsubscribe = cache.subscribe(0, callback);
          unsubscribe();

          cache.addData(0, ONE_HOUR_S, [1, 2, 3]);
          cache.addData(ONE_HOUR_S, 2 * ONE_HOUR_S, [4, 5, 6]);

          expect(callback).not.toHaveBeenCalled();
        });
      },
    );
  });
});

describe('HourlyDataCache with IndexedDB', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should load cache from IndexedDB on initialization', async () => {
    mockedCache.has.mockResolvedValue(true);

    const sec = Date.now() / 1000;
    const nowHour = Math.floor(sec / ONE_HOUR_S);
    mockedCache.get.mockResolvedValue({
      value: {
        version: VERSION,
        cache: new Map([[nowHour, [{start: nowHour, end: nowHour + ONE_HOUR_S, data: [1, 2, 3]}]]]),
      },
    });

    const cache = new HourlyDataCache<number>({id: 'test', version: VERSION});

    await cache.loadCacheFromIndexedDB();

    expect(cache.getHourData(sec)).toEqual([1, 2, 3]);
    expect(mockedCache.has).toHaveBeenCalledWith('hourlyData');
    expect(mockedCache.get).toHaveBeenCalledWith('hourlyData');
  });

  it('should save cache to IndexedDB when data is added', async () => {
    const cache = new HourlyDataCache<number>({id: 'test', version: VERSION});

    cache.addData(0, ONE_HOUR_S, [1, 2, 3]);

    const mockCallArgs = mockedCache.set.mock.calls[0];
    const map = mockCallArgs[1];
    expect(map.cache).toEqual(
      new Map<number, {data: number[]; end: number; start: number}[]>([
        [0, [{data: [1, 2, 3], end: 3600, start: 0}]],
      ]),
    );
  });

  it('should clear old entries from the cache and save to IndexedDB', async () => {
    const eightDaysAgo = Date.now() / 1000 - 8 * 24 * 60 * 60;
    const sixDaysAgo = Date.now() / 1000 - 6 * 24 * 60 * 60;

    mockedCache.has.mockResolvedValue(true);
    mockedCache.get.mockResolvedValue({
      value: {
        version: VERSION,
        cache: new Map([
          [
            Math.floor(eightDaysAgo / ONE_HOUR_S),
            [{start: eightDaysAgo, end: eightDaysAgo + ONE_HOUR_S, data: [1, 2, 3]}],
          ],
          [
            Math.floor(sixDaysAgo / ONE_HOUR_S),
            [{start: sixDaysAgo, end: eightDaysAgo + ONE_HOUR_S, data: [1, 2, 3]}],
          ],
        ]),
      },
    });

    const cache = new HourlyDataCache<number>({id: 'test', version: VERSION});

    await cache.loadCacheFromIndexedDB();

    expect(cache.getHourData(sixDaysAgo)).toEqual([1, 2, 3]);
    expect(cache.getHourData(eightDaysAgo)).toEqual([]);
  });
});
