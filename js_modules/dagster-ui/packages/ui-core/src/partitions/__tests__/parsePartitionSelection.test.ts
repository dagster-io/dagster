/* eslint-disable jest/no-conditional-expect */
import {parsePartitionSelection} from '../parsePartitionSelection';

describe('parsePartitionSelection', () => {
  describe('single keys', () => {
    it('parses simple unquoted key', () => {
      const result = parsePartitionSelection('partition01');
      expect(result).toEqual([{type: 'single', key: 'partition01'}]);
    });

    it('parses date-formatted key', () => {
      const result = parsePartitionSelection('2024-01-01');
      expect(result).toEqual([{type: 'single', key: '2024-01-01'}]);
    });

    it('parses key with underscore', () => {
      const result = parsePartitionSelection('my_partition_key');
      expect(result).toEqual([{type: 'single', key: 'my_partition_key'}]);
    });

    it('parses key with colon', () => {
      const result = parsePartitionSelection('region:us-east-1');
      expect(result).toEqual([{type: 'single', key: 'region:us-east-1'}]);
    });

    it('parses key with forward slash', () => {
      const result = parsePartitionSelection('path/to/resource');
      expect(result).toEqual([{type: 'single', key: 'path/to/resource'}]);
    });

    it('parses key with at sign', () => {
      const result = parsePartitionSelection('user@domain');
      expect(result).toEqual([{type: 'single', key: 'user@domain'}]);
    });

    it('parses quoted key with comma', () => {
      const result = parsePartitionSelection('"my,key"');
      expect(result).toEqual([{type: 'single', key: 'my,key'}]);
    });

    it('parses quoted key with brackets', () => {
      const result = parsePartitionSelection('"[special]"');
      expect(result).toEqual([{type: 'single', key: '[special]'}]);
    });

    it('parses quoted key with escaped quote', () => {
      const result = parsePartitionSelection('"say\\"hello\\""');
      expect(result).toEqual([{type: 'single', key: 'say"hello"'}]);
    });

    it('parses quoted key with ellipsis', () => {
      const result = parsePartitionSelection('"data...backup"');
      expect(result).toEqual([{type: 'single', key: 'data...backup'}]);
    });

    it('parses quoted key with asterisk', () => {
      const result = parsePartitionSelection('"file*.txt"');
      expect(result).toEqual([{type: 'single', key: 'file*.txt'}]);
    });

    it('parses quoted key with backslash', () => {
      const result = parsePartitionSelection('"path\\\\to\\\\file"');
      expect(result).toEqual([{type: 'single', key: 'path\\to\\file'}]);
    });

    it('parses quoted key with dot (partition keys with dots must be quoted)', () => {
      const result = parsePartitionSelection('"key.with.dots"');
      expect(result).toEqual([{type: 'single', key: 'key.with.dots'}]);
    });
  });

  describe('ranges', () => {
    it('parses simple range', () => {
      const result = parsePartitionSelection('[2024-01-01...2025-01-01]');
      expect(result).toEqual([{type: 'range', start: '2024-01-01', end: '2025-01-01'}]);
    });

    it('parses range with quoted keys', () => {
      const result = parsePartitionSelection('["start,key"..."end,key"]');
      expect(result).toEqual([{type: 'range', start: 'start,key', end: 'end,key'}]);
    });

    it('parses range with mixed quoting (start unquoted, end quoted)', () => {
      const result = parsePartitionSelection('[2024-01-01..."end,key"]');
      expect(result).toEqual([{type: 'range', start: '2024-01-01', end: 'end,key'}]);
    });

    it('parses range with mixed quoting (start quoted, end unquoted)', () => {
      const result = parsePartitionSelection('["start,key"...2025-01-01]');
      expect(result).toEqual([{type: 'range', start: 'start,key', end: '2025-01-01'}]);
    });

    it('parses range with quoted ellipsis in key', () => {
      const result = parsePartitionSelection('["start...value"..."end...value"]');
      expect(result).toEqual([{type: 'range', start: 'start...value', end: 'end...value'}]);
    });
  });

  describe('wildcards', () => {
    it('parses prefix wildcard', () => {
      const result = parsePartitionSelection('2024-*');
      expect(result).toEqual([{type: 'wildcard', prefix: '2024-', suffix: ''}]);
    });

    it('parses suffix wildcard', () => {
      const result = parsePartitionSelection('*-production');
      expect(result).toEqual([{type: 'wildcard', prefix: '', suffix: '-production'}]);
    });

    it('parses infix wildcard', () => {
      const result = parsePartitionSelection('prefix-*-suffix');
      expect(result).toEqual([{type: 'wildcard', prefix: 'prefix-', suffix: '-suffix'}]);
    });

    it('parses standalone asterisk', () => {
      const result = parsePartitionSelection('*');
      expect(result).toEqual([{type: 'wildcard', prefix: '', suffix: ''}]);
    });
  });

  describe('lists', () => {
    it('parses comma-separated keys', () => {
      const result = parsePartitionSelection('key1, key2, key3');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
        {type: 'single', key: 'key3'},
      ]);
    });

    it('parses list without spaces', () => {
      const result = parsePartitionSelection('key1,key2,key3');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
        {type: 'single', key: 'key3'},
      ]);
    });

    it('parses mixed list with range', () => {
      const result = parsePartitionSelection('key1, [2024-01-01...2024-01-31], key2');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'range', start: '2024-01-01', end: '2024-01-31'},
        {type: 'single', key: 'key2'},
      ]);
    });

    it('parses mixed list with wildcard', () => {
      const result = parsePartitionSelection('key1, 2024-*, key2');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'wildcard', prefix: '2024-', suffix: ''},
        {type: 'single', key: 'key2'},
      ]);
    });

    it('parses list with quoted and unquoted keys', () => {
      const result = parsePartitionSelection('simple, "complex,key", another');
      expect(result).toEqual([
        {type: 'single', key: 'simple'},
        {type: 'single', key: 'complex,key'},
        {type: 'single', key: 'another'},
      ]);
    });

    it('parses list with all three types', () => {
      const result = parsePartitionSelection('"special,key", [2024-01-01...2024-12-31], 2025-*');
      expect(result).toEqual([
        {type: 'single', key: 'special,key'},
        {type: 'range', start: '2024-01-01', end: '2024-12-31'},
        {type: 'wildcard', prefix: '2025-', suffix: ''},
      ]);
    });

    it('handles empty items between commas (backward compatibility)', () => {
      const result = parsePartitionSelection('key1, , key2');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
      ]);
    });

    it('handles trailing comma', () => {
      const result = parsePartitionSelection('key1, key2,');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
      ]);
    });

    it('handles leading comma', () => {
      const result = parsePartitionSelection(',key1, key2');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
      ]);
    });
  });

  describe('edge cases', () => {
    it('handles empty string', () => {
      const result = parsePartitionSelection('');
      expect(result).toEqual([]);
    });

    it('handles whitespace only', () => {
      const result = parsePartitionSelection('   ');
      expect(result).toEqual([]);
    });

    it('handles tabs and newlines', () => {
      const result = parsePartitionSelection('\t\n');
      expect(result).toEqual([]);
    });

    it('handles extra whitespace around items', () => {
      const result = parsePartitionSelection('  key1  ,  key2  ');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
      ]);
    });

    it('handles whitespace inside range brackets', () => {
      const result = parsePartitionSelection('[  2024-01-01  ...  2024-12-31  ]');
      expect(result).toEqual([{type: 'range', start: '2024-01-01', end: '2024-12-31'}]);
    });
  });

  describe('error cases', () => {
    it('returns error for unclosed quote', () => {
      const result = parsePartitionSelection('"unclosed');
      expect(result).toBeInstanceOf(Error);
    });

    it('returns error for unclosed bracket', () => {
      const result = parsePartitionSelection('[2024-01-01...2024-12-31');
      expect(result).toBeInstanceOf(Error);
    });

    it('returns error for missing range end', () => {
      const result = parsePartitionSelection('[2024-01-01...]');
      expect(result).toBeInstanceOf(Error);
    });
  });

  describe('backward compatibility', () => {
    // These tests ensure existing unquoted selections continue to work
    it('handles existing date partitions', () => {
      const result = parsePartitionSelection('2022-01-01, 2022-01-02, 2022-01-03');
      expect(result).not.toBeInstanceOf(Error);
      expect(result).toHaveLength(3);
    });

    it('handles existing range syntax', () => {
      const result = parsePartitionSelection('[2022-01-01...2022-01-10]');
      expect(result).not.toBeInstanceOf(Error);
      if (!(result instanceof Error)) {
        expect(result[0]).toEqual({type: 'range', start: '2022-01-01', end: '2022-01-10'});
      }
    });

    it('handles existing wildcard syntax', () => {
      const result = parsePartitionSelection('2022-01-*');
      expect(result).not.toBeInstanceOf(Error);
      if (!(result instanceof Error)) {
        expect(result[0]).toEqual({type: 'wildcard', prefix: '2022-01-', suffix: ''});
      }
    });

    it('handles keys with hyphens (common in date partitions)', () => {
      const result = parsePartitionSelection('us-east-1');
      expect(result).toEqual([{type: 'single', key: 'us-east-1'}]);
    });

    it('handles keys with numbers', () => {
      const result = parsePartitionSelection('partition123');
      expect(result).toEqual([{type: 'single', key: 'partition123'}]);
    });
  });
});
