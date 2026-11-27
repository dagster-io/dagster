import dayjs from 'dayjs';

import {
  RECENT_PARTITIONS_DAYS,
  filterPartitionKeysByDate,
  recentPartitionsFilter,
} from '../partitionDateFilter';

const dailyKeys = (count: number, endingOn: dayjs.Dayjs) =>
  Array.from({length: count}, (_, i) =>
    endingOn.subtract(count - 1 - i, 'day').format('YYYY-MM-DD'),
  );

describe('filterPartitionKeysByDate', () => {
  it('returns all keys when no filter is applied', () => {
    const keys = ['2024-01-01', '2024-01-02'];
    expect(filterPartitionKeysByDate(keys, null)).toEqual(keys);
  });

  it('includes the keys on the boundaries of the window', () => {
    const filter = {
      from: dayjs('2024-01-02').startOf('day'),
      to: dayjs('2024-01-04').endOf('day'),
      label: 'Custom',
    };
    expect(
      filterPartitionKeysByDate(
        ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        filter,
      ),
    ).toEqual(['2024-01-02', '2024-01-03', '2024-01-04']);
  });

  it('groups sub-daily keys by their date prefix', () => {
    const filter = {
      from: dayjs('2024-01-02').startOf('day'),
      to: dayjs('2024-01-02').endOf('day'),
      label: 'Custom',
    };
    expect(
      filterPartitionKeysByDate(
        ['2024-01-01-2300', '2024-01-02-0000', '2024-01-02-2300', '2024-01-03-0000'],
        filter,
      ),
    ).toEqual(['2024-01-02-0000', '2024-01-02-2300']);
  });

  it('drops keys that have no date prefix', () => {
    const filter = {
      from: dayjs('2024-01-01').startOf('day'),
      to: dayjs('2024-12-31').endOf('day'),
      label: 'Custom',
    };
    expect(filterPartitionKeysByDate(['2024-01-02', 'us-east-1'], filter)).toEqual(['2024-01-02']);
  });
});

describe('recentPartitionsFilter', () => {
  it('keeps recent daily partitions and hides ones older than the window', () => {
    const filter = recentPartitionsFilter('UTC');
    // Anchored on the window's own last day, so the assertions hold whatever
    // zone the host runs in.
    const lastDay = dayjs(filter.to.format('YYYY-MM-DD'));
    const keys = dailyKeys(RECENT_PARTITIONS_DAYS * 3, lastDay);
    const visible = filterPartitionKeysByDate(keys, filter);

    expect(visible).toContain(lastDay.format('YYYY-MM-DD'));
    expect(visible).not.toContain(
      lastDay.subtract(RECENT_PARTITIONS_DAYS + 1, 'day').format('YYYY-MM-DD'),
    );
    expect(visible.length).toBeLessThan(keys.length);
  });

  // Zones either side of UTC, so the window's calendar day differs from the
  // host's in both directions.
  it.each(['Asia/Tokyo', 'America/Los_Angeles'])(
    'includes both boundary days of the window in %s',
    (timezone) => {
      const filter = recentPartitionsFilter(timezone);
      const firstDay = filter.from.format('YYYY-MM-DD');
      const lastDay = filter.to.format('YYYY-MM-DD');

      const visible = filterPartitionKeysByDate(
        [
          dayjs(firstDay).subtract(1, 'day').format('YYYY-MM-DD'),
          firstDay,
          lastDay,
          dayjs(lastDay).add(1, 'day').format('YYYY-MM-DD'),
        ],
        filter,
      );

      expect(visible).toEqual([firstDay, lastDay]);
    },
  );
});
