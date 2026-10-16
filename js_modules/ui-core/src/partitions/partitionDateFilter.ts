import dayjs from 'dayjs';

import {parsePartitionDate} from './isDateFormattedPartitions';
import '../util/dayjsExtensions';

/**
 * A date window used to narrow the partition keys shown in partition selection
 * UI. The label travels with the range so the dropdown and any surrounding
 * messaging describe the same window without re-deriving it.
 */
export interface PartitionDateFilter {
  from: dayjs.Dayjs;
  to: dayjs.Dayjs;
  label: string;
}

/**
 * Window applied by default when choosing partitions for a backfill. Wide
 * enough to cover a meaningful stretch of daily partitions while still cutting
 * an hourly asset down to a manageable number of keys.
 */
export const RECENT_PARTITIONS_DAYS = 90;

export const RECENT_PARTITIONS_LABEL = `Last ${RECENT_PARTITIONS_DAYS} days`;

export const recentPartitionsFilter = (timezone: string): PartitionDateFilter => ({
  from: dayjs().tz(timezone).subtract(RECENT_PARTITIONS_DAYS, 'day').startOf('day'),
  to: dayjs().tz(timezone).endOf('day'),
  label: RECENT_PARTITIONS_LABEL,
});

/**
 * Keys without a parseable date prefix are excluded when a filter is applied.
 *
 * The comparison is by calendar date rather than by instant. A partition key
 * names a day, not a moment, and the window's days are read in the window's own
 * timezone, so both boundary days are included whichever zone the viewer is in.
 * Zero-padded YYYY-MM-DD sorts chronologically as a string.
 */
export const filterPartitionKeysByDate = (
  partitionKeys: string[],
  filter: PartitionDateFilter | null,
): string[] => {
  if (!filter) {
    return partitionKeys;
  }
  const fromDay = filter.from.format('YYYY-MM-DD');
  const toDay = filter.to.format('YYYY-MM-DD');
  return partitionKeys.filter((key) => {
    const parsed = parsePartitionDate(key);
    if (!parsed) {
      return false;
    }
    const day = parsed.format('YYYY-MM-DD');
    return day >= fromDay && day <= toDay;
  });
};
