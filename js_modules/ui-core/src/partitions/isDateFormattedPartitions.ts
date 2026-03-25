/**
 * Utility to detect whether partition keys begin with a date prefix (YYYY-MM-DD)
 * and to extract a day-level dayjs from each key. Used by DimensionRangeWizard
 * to offer a date range filter that narrows the visible set of partitions.
 *
 * Keys like "2026-05-05", "2026-05-05T00:00:00", and "2026-05-05-0000" all
 * resolve to the same day (2026-05-05). We intentionally ignore anything after
 * the date prefix so that sub-daily partitions are grouped by day.
 */

import dayjs from 'dayjs';

/**
 * Matches a leading YYYY-MM-DD at the start of a string. The date may be
 * followed by anything (T, space, dash, etc.) or nothing at all.
 */
const DATE_PREFIX_RE = /^(\d{4})-(\d{2})-(\d{2})($|[T \-])/;

/**
 * Parse the date prefix of a partition key into a dayjs instance at day
 * granularity. Returns null if the key doesn't start with a valid date.
 *
 * Uses plain `dayjs()` (not `dayjs.utc()`) so that the literal date values
 * are preserved regardless of the user's timezone.
 */
export function parsePartitionDate(key: string): dayjs.Dayjs | null {
  const trimmed = key.trim();
  const m = DATE_PREFIX_RE.exec(trimmed);
  if (!m) {
    return null;
  }

  const dateStr = `${m[1]}-${m[2]}-${m[3]}`;
  const d = dayjs(dateStr);

  // Roundtrip check: dayjs is lenient (month 13 wraps), so verify the date
  // part survives formatting.
  if (d.isValid() && d.format('YYYY-MM-DD') === dateStr) {
    return d;
  }
  return null;
}

export interface DatePartitionInfo {
  /** Whether the partition keys start with date prefixes. */
  isDateFormatted: true;
  /**
   * Whether the partitions are sub-daily (e.g. hourly or per-minute).
   * True when the first 6+ keys all resolve to the same calendar date.
   */
  isHighResolution: boolean;
}

/**
 * Detect whether the given partition keys start with date prefixes.
 * Samples keys from the beginning, middle, and end for efficiency.
 *
 * Returns a {@link DatePartitionInfo} if all sampled keys have a valid date
 * prefix, or null if the keys are not date-formatted.
 */
export function detectDatePartitions(partitionKeys: string[]): DatePartitionInfo | null {
  if (partitionKeys.length === 0) {
    return null;
  }

  const sampled = sampleKeys(partitionKeys);
  if (!sampled.every((key) => parsePartitionDate(key) !== null)) {
    return null;
  }

  // Check if the first two keys share the same calendar date — if so, the
  // partition scheme is sub-daily (hourly, per-minute, etc.).
  let isHighResolution = false;
  if (partitionKeys.length >= 2) {
    const first = parsePartitionDate(partitionKeys[0] ?? '');
    const second = parsePartitionDate(partitionKeys[1] ?? '');
    if (first && second) {
      isHighResolution = first.format('YYYY-MM-DD') === second.format('YYYY-MM-DD');
    }
  }

  return {isDateFormatted: true, isHighResolution};
}

/**
 * @deprecated Use {@link detectDatePartitions} instead.
 */
export function isDateFormattedPartitions(partitionKeys: string[]): boolean {
  return detectDatePartitions(partitionKeys) !== null;
}

function sampleKeys(keys: string[]): string[] {
  if (keys.length <= 5) {
    return keys;
  }
  const mid = Math.floor(keys.length / 2);
  const first = keys[0];
  const second = keys[1];
  const middle = keys[mid];
  const penultimate = keys[keys.length - 2];
  const last = keys[keys.length - 1];
  if (!first || !second || !middle || !penultimate || !last) {
    return [];
  }
  return [first, second, middle, penultimate, last];
}
