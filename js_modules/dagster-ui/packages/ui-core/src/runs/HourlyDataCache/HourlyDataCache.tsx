import {cache} from 'idb-lru-cache';

type TimeWindow<T> = {start: number; end: number; data: T[]};

export const ONE_HOUR_S = 60 * 60;

type Subscription<T> = (data: T[]) => void;

export const defaultOptions = {
  expiry: new Date('3030-01-01'), // never expire,
};

type CacheType<T> = {
  version: string | number;
  cache: InstanceType<typeof HourlyDataCache<T>>['cache'];
};

export class HourlyDataCache<T> {
  private cache: Map<number, Array<TimeWindow<T>>> = new Map();
  private subscriptions: Array<{hour: number; callback: Subscription<T>}> = [];
  private indexedDBCache?: ReturnType<typeof cache<string, CacheType<T>>>;
  private indexedDBKey: string;
  private version: string | number;

  /**
   * @param id A unique ID for the hourly data cache in this deployment
   * @param [keyPrefix=''] A unique key identifying the timeline view [incorporating filters, etc.]
   */
  constructor({
    id,
    keyPrefix = '',
    keyMaxCount = 1,
    version,
  }: {
    id?: string | false;
    keyPrefix?: string;
    keyMaxCount?: number;
    version: string | number;
  }) {
    this.version = version;
    this.indexedDBKey = keyPrefix ? `${keyPrefix}-hourlyData` : 'hourlyData';

    if (id) {
      try {
        this.indexedDBCache = cache<string, CacheType<T>>({
          dbName: `HourlyDataCache:${id}`,
          maxCount: keyMaxCount,
        });
        this.loadCacheFromIndexedDB();
        this.clearOldEntries();
      } catch (e) {}
    }
  }

  loadPromise: Promise<void> | undefined;

  public async loadCacheFromIndexedDB() {
    if (!this.indexedDBCache) {
      return;
    }
    if (this.loadPromise) {
      return await this.loadPromise;
    }
    this.loadPromise = new Promise(async (res) => {
      if (!this.indexedDBCache) {
        return;
      }
      if (!(await this.indexedDBCache.has(this.indexedDBKey))) {
        res();
        return;
      }
      const cachedData = await this.indexedDBCache.get(this.indexedDBKey);
      if (cachedData && cachedData.value.version === this.version) {
        this.cache = new Map(cachedData.value.cache);
      }
      res();
    });
    return await this.loadPromise;
  }

  private saveTimeout?: ReturnType<typeof setTimeout>;
  private registeredUnload: boolean = false;
  private async saveCacheToIndexedDB() {
    if (typeof jest !== 'undefined') {
      if (!this.indexedDBCache) {
        return;
      }
      this.indexedDBCache.set(
        this.indexedDBKey,
        {version: this.version, cache: this.cache},
        defaultOptions,
      );
      return;
    }
    clearTimeout(this.saveTimeout);
    this.saveTimeout = setTimeout(() => {
      if (!this.indexedDBCache) {
        return;
      }
      this.indexedDBCache.set(
        this.indexedDBKey,
        {version: this.version, cache: this.cache},
        defaultOptions,
      );
    }, 10000);
    if (!this.registeredUnload) {
      this.registeredUnload = true;
      window.addEventListener('beforeunload', () => {
        if (!this.indexedDBCache) {
          return;
        }
        this.indexedDBCache.set(
          this.indexedDBKey,
          {version: this.version, cache: this.cache},
          defaultOptions,
        );
      });
    }
  }

  public async clearOldEntries() {
    const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const hour = Math.floor(oneWeekAgo / (ONE_HOUR_S * 1000));

    await this.loadCacheFromIndexedDB();
    for (const ts of this.cache.keys()) {
      if (ts < hour) {
        this.cache.delete(ts);
      }
    }
  }

  /**
   * Adds data to the cache for the specified time range.
   * @param start - The start time in seconds.
   * @param end - The end time in seconds.
   * @param data - The data to cache.
   */
  addData(start: number, end: number, data: T[]): void {
    const startHour = Math.floor(start / ONE_HOUR_S);
    const endHour = Math.floor(end / ONE_HOUR_S);

    if (endHour - startHour > 1) {
      throw new Error('Expected all data to fit within an hour');
    }

    this.addPartialData(startHour, start, end, data);
    this.notifySubscribers(startHour);
    this.saveCacheToIndexedDB();
  }

  /**
   * Adds data to the partial cache for a specific hour.
   * @param hour - The hour for which to add data.
   * @param start - The start time in seconds.
   * @param end - The end time in seconds.
   * @param data - The data to cache.
   */
  private addPartialData(hour: number, start: number, end: number, data: T[]): void {
    if (!this.cache.has(hour)) {
      this.cache.set(hour, []);
    }
    this.cache.get(hour)!.push({start, end, data});
    this.cache.set(hour, this.mergeIntervals(this.cache.get(hour)!));
  }

  /**
   * Retrieves the data for a specific hour.
   * @param s - The time in seconds.
   * @returns The data for the specified hour.
   */
  getHourData(s: number): T[] {
    const hour = Math.floor(s / ONE_HOUR_S);
    if (this.cache.has(hour)) {
      return this.cache.get(hour)!.flatMap((interval) => interval.data);
    }
    return [];
  }

  /**
   * Returns the missing ranges for a specific hour.
   * @param s - The time in seconds.
   * @returns An array of missing ranges for the specified hour.
   */
  getMissingIntervals(s: number): Array<[number, number]> {
    const hour = Math.floor(s / ONE_HOUR_S);
    if (
      this.cache.has(hour) &&
      this.cache.get(hour)!.length === 1 &&
      this.cache.get(hour)![0]!.end - this.cache.get(hour)![0]!.start === ONE_HOUR_S
    ) {
      return [];
    }

    const missingIntervals: Array<[number, number]> = [];
    const hourStart = hour * ONE_HOUR_S;
    const hourEnd = (hour + 1) * ONE_HOUR_S;
    let currentStart = hourStart;

    if (this.cache.has(hour)) {
      for (const {start: cachedStart, end: cachedEnd} of this.cache.get(hour)!) {
        if (cachedStart > currentStart) {
          missingIntervals.push([currentStart, cachedStart]);
        }
        currentStart = Math.max(currentStart, cachedEnd);
      }
    }

    if (currentStart < hourEnd) {
      missingIntervals.push([currentStart, hourEnd]);
    }

    return missingIntervals;
  }

  /**
   * Checks if a range is completely cached.
   * @param start - The start time in seconds.
   * @param end - The end time in seconds.
   * @returns True if the range is completely cached, false otherwise.
   */
  isCompleteRange(start: number, end: number): boolean {
    const startHour = Math.floor(start / ONE_HOUR_S);
    const endHour = Math.floor(end / ONE_HOUR_S);

    if (endHour - startHour > 1) {
      throw new Error('Expected the input range to be within a single hour');
    }

    if (this.cache.has(startHour)) {
      const intervals = this.cache.get(startHour)!;
      let currentStart = start;

      for (const {start: cachedStart, end: cachedEnd} of intervals) {
        if (cachedStart > currentStart) {
          return false;
        }
        if (cachedEnd >= end) {
          return true;
        }
        currentStart = Math.max(currentStart, cachedEnd);
      }

      return currentStart >= end;
    }

    return false;
  }

  /**
   * Merges overlapping intervals.
   * @param intervals - The intervals to merge.
   * @returns An array of merged intervals.
   */
  private mergeIntervals(intervals: Array<TimeWindow<T>>): Array<TimeWindow<T>> {
    if (intervals.length === 0) {
      return [];
    }

    intervals.sort((a, b) => a.start - b.start);
    const mergedIntervals: Array<TimeWindow<T>> = [intervals[0]!];

    for (const current of intervals.slice(1)) {
      const lastMerged = mergedIntervals[mergedIntervals.length - 1]!;

      if (current.start <= lastMerged.end) {
        lastMerged.end = Math.max(lastMerged.end, current.end);
        lastMerged.data = lastMerged.data.concat(current.data);
      } else {
        mergedIntervals.push(current);
      }
    }

    return mergedIntervals;
  }

  /**
   * Subscribes to data added to a specific hourly bucket and subsequent hours.
   * @param startHour - The hour bucket to subscribe to.
   * @param callback - The callback function to notify when new data is added.
   */
  subscribe(ts: number, callback: Subscription<T>) {
    const startHour = Math.floor(ts / ONE_HOUR_S);
    const sub = {hour: startHour, callback};
    this.subscriptions.push(sub);
    this.notifyExistingData(startHour, callback);

    return () => {
      this.subscriptions = this.subscriptions.filter((subB) => subB !== sub);
    };
  }

  /**
   * Notifies subscribers of new data added to a specific hour and subsequent hours.
   * @param hour - The hour bucket to notify subscribers of.
   * @param data - The new data added.
   */
  private notifySubscribers(hour: number): void {
    for (const {hour: subHour, callback} of this.subscriptions) {
      if (hour >= subHour) {
        const combinedData = this.getCombinedData(subHour);
        callback(combinedData);
      }
    }
  }

  /**
   * Notifies a new subscriber of all existing data for the subscribed hour and subsequent hours.
   * @param startHour - The starting hour for the subscription.
   * @param callback - The callback function to notify with existing data.
   */
  private notifyExistingData(startHour: number, callback: Subscription<T>): void {
    const combinedData = this.getCombinedData(startHour);
    if (combinedData.length > 0) {
      callback(combinedData);
    }
  }

  /**
   * Combines data from the given hour and subsequent hours.
   * @param startHour - The starting hour.
   * @returns Combined data.
   */
  private getCombinedData(startHour: number): T[] {
    let combinedData: T[] = [];
    for (const [hour, intervals] of this.cache) {
      if (hour >= startHour) {
        combinedData = combinedData.concat(intervals.flatMap((interval) => interval.data));
      }
    }
    return combinedData;
  }
}

/**
 * Breaks a time range into hourly buckets.
 * @param startTime - The start time in seconds.
 * @param endTime - The end time in seconds.
 * @returns An array of [start, end] pairs representing each hourly bucket.
 */
export function getHourlyBuckets(startTime: number, endTime: number): [number, number][] {
  const buckets: [number, number][] = [];

  // Convert start and end times to the number of hours since epoch
  const startHour = Math.floor(startTime / ONE_HOUR_S) * ONE_HOUR_S;

  // Handle the first partial bucket
  if (startTime !== startHour) {
    const firstBucketEnd = startHour + ONE_HOUR_S;
    buckets.push([startTime, Math.min(firstBucketEnd, endTime)]);
  }

  // Add full hourly buckets
  let currentStart = startHour + (startTime === startHour ? 0 : ONE_HOUR_S);
  while (currentStart + ONE_HOUR_S <= endTime) {
    const nextHour = currentStart + ONE_HOUR_S;
    buckets.push([currentStart, nextHour]);
    currentStart = nextHour;
  }

  // Handle the last partial bucket
  if (currentStart < endTime) {
    buckets.push([currentStart, endTime]);
  }

  return buckets;
}
