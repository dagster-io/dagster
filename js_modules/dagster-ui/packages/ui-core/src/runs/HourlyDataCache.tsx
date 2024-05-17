type TimeWindow<T> = {start: number; end: number; data: T[]};

export const ONE_HOUR = 3600 * 1000;
export class HourlyDataCache<T> {
  private hourlyCache: Map<number, T[]> = new Map();
  private partialCache: Map<number, Array<TimeWindow<T>>> = new Map();

  addToCache(start: number, end: number, data: T[]): void {
    const startHour = Math.floor(start / ONE_HOUR);
    const endHour = Math.floor(end / ONE_HOUR);

    if (startHour === endHour) {
      // If the data is within a single hour, add to partial cache
      this.addPartialCache(startHour, start, end, data);
    } else {
      // If the data spans multiple hours, handle each hour separately
      throw new Error('Expected all data to fit within an hour');
    }

    // Promote to hourly cache if full hours are complete
    this.promoteToHourlyCache();
  }

  private addPartialCache(hour: number, start: number, end: number, data: T[]): void {
    if (!this.partialCache.has(hour)) {
      this.partialCache.set(hour, []);
    }
    this.partialCache.get(hour)!.push({start, end, data});
    this.partialCache.set(hour, this.mergeIntervals(this.partialCache.get(hour)!));
  }

  private promoteToHourlyCache(): void {
    const completedHours: number[] = [];
    for (const [hour, intervals] of this.partialCache) {
      if (intervals.length === 1 && intervals[0]!.end - intervals[0]!.start === ONE_HOUR - 1) {
        // Check if the hour is complete
        this.hourlyCache.set(hour, intervals[0]!.data);
        completedHours.push(hour);
      }
    }
    // Remove promoted hours from partial cache
    for (const hour of completedHours) {
      this.partialCache.delete(hour);
    }
  }

  getDataForHour(ms: number): T[] {
    const hour = Math.floor(ms / ONE_HOUR);
    if (this.hourlyCache.has(hour)) {
      return this.hourlyCache.get(hour)!;
    }
    if (this.partialCache.has(hour)) {
      return this.partialCache.get(hour)!.flatMap((interval) => interval.data);
    }
    return [];
  }

  getMissingRangeForHour(ms: number): Array<[number, number]> {
    const hour = Math.floor(ms / ONE_HOUR);
    if (this.hourlyCache.has(hour)) {
      return [];
    }
    const missingRanges: Array<[number, number]> = [];
    const hourStart = hour * ONE_HOUR;
    const hourEnd = (hour + 1) * ONE_HOUR;

    if (!this.partialCache.has(hour)) {
      return [[hourStart, hourEnd]];
    }

    let currentStart = hourStart;
    for (const {start: cachedStart, end: cachedEnd} of this.partialCache.get(hour)!) {
      if (cachedStart > currentStart) {
        missingRanges.push([currentStart, cachedStart]);
      }
      currentStart = Math.max(currentStart, cachedEnd);
    }

    if (currentStart < hourEnd) {
      missingRanges.push([currentStart, hourEnd]);
    }

    return missingRanges;
  }

  isRangeComplete(start: number, end: number): boolean {
    const startHour = Math.floor(start / ONE_HOUR);
    const endHour = Math.floor(end / ONE_HOUR);

    if (startHour !== endHour) {
      throw new Error('Expected the input range to be within a single hour');
    }

    if (this.hourlyCache.has(startHour)) {
      return true;
    }
    if (!this.partialCache.has(startHour)) {
      return false;
    }

    let currentStart = start;
    for (const {start: cachedStart, end: cachedEnd} of this.partialCache.get(startHour)!) {
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
export function breakIntoHourlyBuckets(startTime: number, endTime: number): [number, number][] {
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
