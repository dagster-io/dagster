import dayjs from 'dayjs';

import {
  detectDatePartitions,
  isDateFormattedPartitions,
  parsePartitionDate,
} from '../isDateFormattedPartitions';

describe('parsePartitionDate', () => {
  it('parses YYYY-MM-DD format', () => {
    const d = parsePartitionDate('2024-01-15');
    expect(d).not.toBeNull();
    if (!d) {
      return;
    }
    expect(d.year()).toBe(2024);
    expect(d.month()).toBe(0); // January
    expect(d.date()).toBe(15);
  });

  it('parses date prefix from datetime keys (T separator)', () => {
    const d = parsePartitionDate('2024-06-15T14:30:00');
    expect(d).not.toBeNull();
    if (!d) {
      return;
    }
    expect(d.year()).toBe(2024);
    expect(d.month()).toBe(5); // June
    expect(d.date()).toBe(15);
  });

  it('parses date prefix from datetime keys (space separator)', () => {
    const d = parsePartitionDate('2024-06-15 14:30:00');
    expect(d).not.toBeNull();
    if (!d) {
      return;
    }
    expect(d.year()).toBe(2024);
    expect(d.date()).toBe(15);
  });

  it('parses date prefix from dash-suffixed keys', () => {
    const d = parsePartitionDate('2026-05-05-0000');
    expect(d).not.toBeNull();
    if (!d) {
      return;
    }
    expect(d.year()).toBe(2026);
    expect(d.month()).toBe(4); // May
    expect(d.date()).toBe(5);
  });

  it('returns day-level granularity regardless of suffix', () => {
    const a = parsePartitionDate('2024-03-10T08:00:00');
    const b = parsePartitionDate('2024-03-10T20:00:00');
    const c = parsePartitionDate('2024-03-10-something');
    const d = parsePartitionDate('2024-03-10');
    expect(a).not.toBeNull();
    expect(b).not.toBeNull();
    expect(c).not.toBeNull();
    expect(d).not.toBeNull();
    if (!a || !b || !c || !d) {
      return;
    }
    // All resolve to the same day
    expect(a.format('YYYY-MM-DD')).toBe('2024-03-10');
    expect(b.format('YYYY-MM-DD')).toBe('2024-03-10');
    expect(c.format('YYYY-MM-DD')).toBe('2024-03-10');
    expect(d.format('YYYY-MM-DD')).toBe('2024-03-10');
  });

  it('returns null for non-date strings', () => {
    expect(parsePartitionDate('hello')).toBeNull();
    expect(parsePartitionDate('partition_1')).toBeNull();
    expect(parsePartitionDate('abc-123')).toBeNull();
    expect(parsePartitionDate('')).toBeNull();
    expect(parsePartitionDate('  ')).toBeNull();
  });

  it('returns null for partial date-like strings', () => {
    expect(parsePartitionDate('2024')).toBeNull();
    expect(parsePartitionDate('2024-1')).toBeNull();
    expect(parsePartitionDate('2024-01-1')).toBeNull();
    expect(parsePartitionDate('01-15-2024')).toBeNull();
  });

  it('returns null for invalid dates that match regex', () => {
    expect(parsePartitionDate('2024-13-01')).toBeNull();
  });
});

describe('isDateFormattedPartitions', () => {
  it('returns true for date keys', () => {
    expect(isDateFormattedPartitions(['2024-01-01', '2024-01-02', '2024-01-03'])).toBe(true);
  });

  it('returns true for datetime keys', () => {
    expect(
      isDateFormattedPartitions([
        '2024-01-01T00:00:00',
        '2024-01-01T01:00:00',
        '2024-01-01T02:00:00',
      ]),
    ).toBe(true);
  });

  it('returns true for dash-suffixed keys', () => {
    expect(
      isDateFormattedPartitions(['2026-05-05-0000', '2026-05-05-0001', '2026-05-06-0000']),
    ).toBe(true);
  });

  it('returns false for non-date keys', () => {
    expect(isDateFormattedPartitions(['partition_a', 'partition_b', 'partition_c'])).toBe(false);
  });

  it('returns false for empty array', () => {
    expect(isDateFormattedPartitions([])).toBe(false);
  });

  it('returns false when some keys are not dates', () => {
    expect(isDateFormattedPartitions(['2024-01-01', '2024-01-02', 'not-a-date'])).toBe(false);
  });

  it('works with large arrays by sampling', () => {
    const keys = Array.from({length: 1000}, (_, i) =>
      dayjs('2020-01-01').add(i, 'day').format('YYYY-MM-DD'),
    );
    expect(isDateFormattedPartitions(keys)).toBe(true);
  });

  it('detects single key', () => {
    expect(isDateFormattedPartitions(['2024-01-01'])).toBe(true);
  });
});

describe('detectDatePartitions', () => {
  it('returns null for non-date keys', () => {
    expect(detectDatePartitions(['partition_a', 'partition_b'])).toBeNull();
  });

  it('returns null for empty array', () => {
    expect(detectDatePartitions([])).toBeNull();
  });

  it('returns isHighResolution: false for daily partitions', () => {
    const keys = Array.from({length: 10}, (_, i) =>
      dayjs('2024-01-01').add(i, 'day').format('YYYY-MM-DD'),
    );
    const result = detectDatePartitions(keys);
    expect(result).not.toBeNull();
    expect(result?.isHighResolution).toBe(false);
  });

  it('returns isHighResolution: true for hourly partitions', () => {
    const keys = Array.from({length: 24}, (_, i) =>
      dayjs('2024-06-15T00:00:00').add(i, 'hour').format('YYYY-MM-DDTHH:mm:ss'),
    );
    const result = detectDatePartitions(keys);
    expect(result).not.toBeNull();
    expect(result?.isHighResolution).toBe(true);
  });

  it('returns isHighResolution: true for per-minute partitions', () => {
    const keys = Array.from({length: 60}, (_, i) =>
      dayjs('2024-06-15T12:00:00').add(i, 'minute').format('YYYY-MM-DDTHH:mm:ss'),
    );
    const result = detectDatePartitions(keys);
    expect(result).not.toBeNull();
    expect(result?.isHighResolution).toBe(true);
  });

  it('returns isHighResolution: false when only 1 key', () => {
    const result = detectDatePartitions(['2024-06-15T00:00:00']);
    expect(result).not.toBeNull();
    expect(result?.isHighResolution).toBe(false);
  });

  it('returns isHighResolution: false when first two keys are different days', () => {
    const keys = ['2024-06-15T00:00:00', '2024-06-16T00:00:00', '2024-06-17T00:00:00'];
    const result = detectDatePartitions(keys);
    expect(result).not.toBeNull();
    expect(result?.isHighResolution).toBe(false);
  });

  it('returns isHighResolution: true for dash-suffixed sub-daily keys', () => {
    const keys = Array.from({length: 10}, (_, i) => `2026-05-05-${i.toString().padStart(4, '0')}`);
    const result = detectDatePartitions(keys);
    expect(result).not.toBeNull();
    expect(result?.isHighResolution).toBe(true);
  });
});
