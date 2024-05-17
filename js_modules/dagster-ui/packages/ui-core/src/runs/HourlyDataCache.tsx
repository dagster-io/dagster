type TimeWindow<T> = {start: number; end: number; data: T[]};

export const ONE_HOUR = 3600 * 1000;

export class HourlyDataCache<T> {
  private cache: Map<number, Array<TimeWindow<T>>> = new Map();

  /**
   * Adds data to the cache for the specified time range.
   * @param start - The start time in milliseconds.
   * @param end - The end time in milliseconds.
   * @param data - The data to cache.
   */
  addData(start: number, end: number, data: T[]): void {
    const startHour = Math.floor(start / ONE_HOUR);
    const endHour = Math.floor(end / ONE_HOUR);

    if (startHour !== endHour) {
      throw new Error('Expected all data to fit within an hour');
    }

    this.addPartialData(startHour, start, end, data);
    this.mergeCompleteHours();
  }

  /**
   * Adds data to the partial cache for a specific hour.
   * @param hour - The hour for which to add data.
   * @param start - The start time in milliseconds.
   * @param end - The end time in milliseconds.
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
   * Merges complete hours in the cache.
   */
  private mergeCompleteHours(): void {
    const completedHours: number[] = [];
    for (const [hour, intervals] of this.cache) {
      if (intervals.length === 1 && intervals[0]!.end - intervals[0]!.start === ONE_HOUR - 1) {
        completedHours.push(hour);
      }
    }
    for (const hour of completedHours) {
      this.cache.set(hour, [
        {
          start: hour * ONE_HOUR,
          end: (hour + 1) * ONE_HOUR - 1,
          data: this.cache.get(hour)![0]!.data,
        },
      ]);
    }
  }

  /**
   * Retrieves the data for a specific hour.
   * @param ms - The time in milliseconds.
   * @returns The data for the specified hour.
   */
  getHourData(ms: number): T[] {
    const hour = Math.floor(ms / ONE_HOUR);
    if (this.cache.has(hour)) {
      return this.cache.get(hour)!.flatMap((interval) => interval.data);
    }
    return [];
  }

  /**
   * Returns the missing ranges for a specific hour.
   * @param ms - The time in milliseconds.
   * @returns An array of missing ranges for the specified hour.
   */
  getMissingIntervals(ms: number): Array<[number, number]> {
    const hour = Math.floor(ms / ONE_HOUR);
    if (
      this.cache.has(hour) &&
      this.cache.get(hour)!.length === 1 &&
      this.cache.get(hour)![0]!.end - this.cache.get(hour)![0]!.start === ONE_HOUR - 1
    ) {
      return [];
    }

    const missingIntervals: Array<[number, number]> = [];
    const hourStart = hour * ONE_HOUR;
    const hourEnd = (hour + 1) * ONE_HOUR;
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
   * @param start - The start time in milliseconds.
   * @param end - The end time in milliseconds.
   * @returns True if the range is completely cached, false otherwise.
   */
  isCompleteRange(start: number, end: number): boolean {
    const startHour = Math.floor(start / ONE_HOUR);
    const endHour = Math.floor(end / ONE_HOUR);

    if (startHour !== endHour) {
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
}

/**
 * Breaks a time range into hourly buckets.
 * @param startTime - The start time in milliseconds.
 * @param endTime - The end time in milliseconds.
 * @returns An array of [start, end] pairs representing each hourly bucket.
 */
export function getHourlyBuckets(startTime: number, endTime: number): [number, number][] {
  const buckets: [number, number][] = [];

  // Convert start and end times to the number of hours since epoch
  const startHour = Math.floor(startTime / ONE_HOUR) * ONE_HOUR;

  // Handle the first partial bucket
  if (startTime !== startHour) {
    const firstBucketEnd = startHour + ONE_HOUR - 1;
    buckets.push([startTime, Math.min(firstBucketEnd, endTime)]);
  }

  // Add full hourly buckets
  let currentStart = startHour + (startTime === startHour ? 0 : ONE_HOUR);
  while (currentStart + ONE_HOUR <= endTime) {
    const nextHour = currentStart + ONE_HOUR;
    buckets.push([currentStart, nextHour - 1]);
    currentStart = nextHour;
  }

  // Handle the last partial bucket
  if (currentStart < endTime) {
    buckets.push([currentStart, endTime]);
  }

  return buckets;
}
