import {
  allPartitionsSpan,
  assembleIntoSpans,
  convertToPartitionSelection,
  escapePartitionKey,
  parseSpanText,
  partitionsToText,
  serializeRange,
  spanTextToSelectionsOrError,
  stringForSpan,
} from '../SpanRepresentation';

const MOCK_PARTITION_STATES = {
  '2022-01-01': 0,
  '2022-01-02': 0,
  '2022-01-03': 0,
  '2022-01-04': 0,
  '2022-01-05': 0,
  '2022-01-06': 0,
  '2022-01-07': 1,
  '2022-01-08': 1,
  '2022-01-09': 1,
  '2022-01-10': 0,
};

const MOCK_PARTITIONS = Object.keys(MOCK_PARTITION_STATES).sort();

describe('SpanRepresentation', () => {
  describe('escapePartitionKey', () => {
    describe('returns simple keys unchanged', () => {
      it('handles alphanumeric key', () => {
        expect(escapePartitionKey('partition01')).toBe('partition01');
      });

      it('handles date-formatted key', () => {
        expect(escapePartitionKey('2024-01-01')).toBe('2024-01-01');
      });

      it('handles key with underscore', () => {
        expect(escapePartitionKey('my_partition')).toBe('my_partition');
      });

      it('handles key with hyphen', () => {
        expect(escapePartitionKey('us-east-1')).toBe('us-east-1');
      });

      it('handles key with colon', () => {
        expect(escapePartitionKey('region:value')).toBe('region:value');
      });

      it('handles key with forward slash', () => {
        expect(escapePartitionKey('path/to/resource')).toBe('path/to/resource');
      });

      it('handles key with at sign', () => {
        expect(escapePartitionKey('user@domain')).toBe('user@domain');
      });
    });

    describe('quotes keys with special characters', () => {
      it('quotes keys with commas', () => {
        expect(escapePartitionKey('my,key')).toBe('"my,key"');
      });

      it('quotes keys with multiple commas', () => {
        expect(escapePartitionKey('a,b,c')).toBe('"a,b,c"');
      });

      it('quotes keys with opening bracket', () => {
        expect(escapePartitionKey('[special')).toBe('"[special"');
      });

      it('quotes keys with closing bracket', () => {
        expect(escapePartitionKey('special]')).toBe('"special]"');
      });

      it('quotes keys with both brackets', () => {
        expect(escapePartitionKey('[special]')).toBe('"[special]"');
      });

      it('quotes keys with dot', () => {
        expect(escapePartitionKey('key.value')).toBe('"key.value"');
      });

      it('quotes keys with asterisk', () => {
        expect(escapePartitionKey('file*.txt')).toBe('"file*.txt"');
      });
    });

    describe('quotes and escapes keys with special escape characters', () => {
      it('escapes and quotes keys with quotes', () => {
        expect(escapePartitionKey('say"hello"')).toBe('"say\\"hello\\""');
      });

      it('escapes and quotes keys with single quote in middle', () => {
        expect(escapePartitionKey('hello"world')).toBe('"hello\\"world"');
      });

      it('escapes and quotes keys with backslash', () => {
        expect(escapePartitionKey('path\\file')).toBe('"path\\\\file"');
      });

      it('escapes and quotes keys with multiple backslashes', () => {
        expect(escapePartitionKey('a\\b\\c')).toBe('"a\\\\b\\\\c"');
      });

      it('escapes both backslash and quote together', () => {
        expect(escapePartitionKey('say\\"hello')).toBe('"say\\\\\\"hello"');
      });
    });

    describe('edge cases', () => {
      it('handles empty string', () => {
        expect(escapePartitionKey('')).toBe('');
      });

      it('handles string with only comma', () => {
        expect(escapePartitionKey(',')).toBe('","');
      });

      it('handles string with only quote', () => {
        expect(escapePartitionKey('"')).toBe('"\\""');
      });

      it('handles string with ellipsis (range delimiter)', () => {
        expect(escapePartitionKey('data...backup')).toBe('"data...backup"');
      });
    });
  });

  describe('serializeRange', () => {
    it('serializes simple range', () => {
      expect(serializeRange('2024-01-01', '2024-12-31')).toBe('[2024-01-01...2024-12-31]');
    });

    it('serializes range with same start and end', () => {
      expect(serializeRange('2024-01-01', '2024-01-01')).toBe('[2024-01-01...2024-01-01]');
    });

    it('serializes range with special characters in start', () => {
      expect(serializeRange('start,key', '2024-12-31')).toBe('["start,key"...2024-12-31]');
    });

    it('serializes range with special characters in end', () => {
      expect(serializeRange('2024-01-01', 'end,key')).toBe('[2024-01-01..."end,key"]');
    });

    it('serializes range with special characters in both', () => {
      expect(serializeRange('start,key', 'end,key')).toBe('["start,key"..."end,key"]');
    });

    it('serializes range with quotes in keys', () => {
      expect(serializeRange('start"key', 'end"key')).toBe('["start\\"key"..."end\\"key"]');
    });

    it('serializes range with brackets in keys', () => {
      expect(serializeRange('[start]', '[end]')).toBe('["[start]"..."[end]"]');
    });

    it('serializes range with ellipsis in keys', () => {
      expect(serializeRange('start...value', 'end...value')).toBe(
        '["start...value"..."end...value"]',
      );
    });
  });

  describe('assembleIntoSpans', () => {
    it('returns spans of each returned value', async () => {
      const result = assembleIntoSpans(
        MOCK_PARTITIONS,
        (key) => MOCK_PARTITION_STATES[key as keyof typeof MOCK_PARTITION_STATES] === 1,
      );
      const expected = [
        {startIdx: 0, endIdx: 5, status: false},
        {startIdx: 6, endIdx: 8, status: true},
        {startIdx: 9, endIdx: 9, status: false},
      ];
      expect(result).toEqual(expected);
    });
  });

  describe('stringForSpan', () => {
    it('returns a single value for a span of length 1', () => {
      expect(stringForSpan({startIdx: 4, endIdx: 4}, MOCK_PARTITIONS)).toEqual('2022-01-05');
    });

    it('returns the [...] range syntax for spans of length > 1', () => {
      expect(stringForSpan({startIdx: 4, endIdx: 8}, MOCK_PARTITIONS)).toEqual(
        '[2022-01-05...2022-01-09]',
      );
    });
  });

  describe('allPartitionsSpan', () => {
    it('should return the full range span', () => {
      expect(allPartitionsSpan({partitionKeys: MOCK_PARTITIONS})).toEqual(
        '[2022-01-01...2022-01-10]',
      );
    });
  });

  describe('parseSpanText', () => {
    it('should parse empty string', () => {
      expect(parseSpanText('')).toEqual([]);
    });

    it('should parse single partition key', () => {
      expect(parseSpanText('2022-01-01')).toEqual([{type: 'single', key: '2022-01-01'}]);
    });

    it('should parse comma-separated single keys', () => {
      expect(parseSpanText('2022-01-01, 2022-01-02,2022-01-03')).toEqual([
        {type: 'single', key: '2022-01-01'},
        {type: 'single', key: '2022-01-02'},
        {type: 'single', key: '2022-01-03'},
      ]);
    });

    it('should parse range syntax', () => {
      expect(parseSpanText('[2022-01-01...2022-01-03]')).toEqual([
        {type: 'range', start: '2022-01-01', end: '2022-01-03'},
      ]);
    });

    it('should parse wildcard syntax', () => {
      expect(parseSpanText('2022-01-*')).toEqual([
        {type: 'wildcard', prefix: '2022-01-', suffix: ''},
      ]);
    });

    it('should parse wildcard with prefix and suffix', () => {
      expect(parseSpanText('2022-*-data')).toEqual([
        {type: 'wildcard', prefix: '2022-', suffix: '-data'},
      ]);
    });

    it('should parse mixed terms', () => {
      expect(parseSpanText('[2022-01-01...2022-01-03], 2022-01-05, 2022-*')).toEqual([
        {type: 'range', start: '2022-01-01', end: '2022-01-03'},
        {type: 'single', key: '2022-01-05'},
        {type: 'wildcard', prefix: '2022-', suffix: ''},
      ]);
    });

    it('should ignore empty terms', () => {
      expect(parseSpanText('2022-01-01, , 2022-01-02')).toEqual([
        {type: 'single', key: '2022-01-01'},
        {type: 'single', key: '2022-01-02'},
      ]);
    });

    it('should handle whitespace correctly', () => {
      expect(parseSpanText('  2022-01-01  ,   [2022-01-02...2022-01-03]  ')).toEqual([
        {type: 'single', key: '2022-01-01'},
        {type: 'range', start: '2022-01-02', end: '2022-01-03'},
      ]);
    });
  });

  describe('convertToPartitionSelection', () => {
    it('should handle empty parsed terms', () => {
      const result = convertToPartitionSelection([], MOCK_PARTITIONS);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual([]);
      expect(result.selectedRanges).toEqual([]);
    });

    it('should convert single key term', () => {
      const parsedTerms = [{type: 'single' as const, key: '2022-01-01'}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 0, key: '2022-01-01'}},
      ]);
    });

    it('should convert range term', () => {
      const parsedTerms = [{type: 'range' as const, start: '2022-01-01', end: '2022-01-03'}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01', '2022-01-02', '2022-01-03']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 2, key: '2022-01-03'}},
      ]);
    });

    it('should convert wildcard term', () => {
      const parsedTerms = [{type: 'wildcard' as const, prefix: '2022-01-0', suffix: ''}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual([
        '2022-01-01',
        '2022-01-02',
        '2022-01-03',
        '2022-01-04',
        '2022-01-05',
        '2022-01-06',
        '2022-01-07',
        '2022-01-08',
        '2022-01-09',
      ]);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 8, key: '2022-01-09'}},
      ]);
    });

    it('should convert wildcard term with prefix and suffix', () => {
      const partitions = ['2022-01-data', '2022-02-data', '2022-03-other', '2022-04-data'];
      const parsedTerms = [{type: 'wildcard' as const, prefix: '2022-', suffix: '-data'}];
      const result = convertToPartitionSelection(parsedTerms, partitions);
      if (result instanceof Error) {
        throw result;
      }
      // The wildcard logic creates consecutive ranges, so it includes all keys in the ranges
      expect(result.selectedKeys).toEqual(['2022-01-data', '2022-02-data', '2022-04-data']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-data'}, end: {idx: 1, key: '2022-02-data'}},
        {start: {idx: 3, key: '2022-04-data'}, end: {idx: 3, key: '2022-04-data'}},
      ]);
    });

    it('should convert multiple terms', () => {
      const parsedTerms = [
        {type: 'range' as const, start: '2022-01-01', end: '2022-01-02'},
        {type: 'single' as const, key: '2022-01-05'},
        {type: 'wildcard' as const, prefix: '2022-01-0', suffix: '7'},
      ];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01', '2022-01-02', '2022-01-05', '2022-01-07']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 1, key: '2022-01-02'}},
        {start: {idx: 4, key: '2022-01-05'}, end: {idx: 4, key: '2022-01-05'}},
        {start: {idx: 6, key: '2022-01-07'}, end: {idx: 6, key: '2022-01-07'}},
      ]);
    });

    it('should deduplicate selected keys', () => {
      const parsedTerms = [
        {type: 'single' as const, key: '2022-01-01'},
        {type: 'range' as const, start: '2022-01-01', end: '2022-01-02'},
        {type: 'single' as const, key: '2022-01-02'},
      ];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01', '2022-01-02']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 0, key: '2022-01-01'}},
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 1, key: '2022-01-02'}},
        {start: {idx: 1, key: '2022-01-02'}, end: {idx: 1, key: '2022-01-02'}},
      ]);
    });

    it('should return error for invalid range start', () => {
      const parsedTerms = [{type: 'range' as const, start: 'invalid', end: '2022-01-03'}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      expect(result).toBeInstanceOf(Error);
      expect((result as Error).message).toBe(
        'Could not find partitions for provided range: invalid...2022-01-03',
      );
    });

    it('should return error for invalid range end', () => {
      const parsedTerms = [{type: 'range' as const, start: '2022-01-01', end: 'invalid'}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      expect(result).toBeInstanceOf(Error);
      expect((result as Error).message).toBe(
        'Could not find partitions for provided range: 2022-01-01...invalid',
      );
    });

    it('should return error for invalid single key', () => {
      const parsedTerms = [{type: 'single' as const, key: 'invalid'}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS);
      expect(result).toBeInstanceOf(Error);
      expect((result as Error).message).toBe('Could not find partition: invalid');
    });

    it('should skip validation when skipPartitionKeyValidation is true', () => {
      const parsedTerms = [{type: 'single' as const, key: 'invalid'}];
      const result = convertToPartitionSelection(parsedTerms, MOCK_PARTITIONS, true);
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['invalid']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: -1, key: 'invalid'}, end: {idx: -1, key: 'invalid'}},
      ]);
    });
  });

  describe('spanTextToSelectionsOrError', () => {
    it('should parse a single value', () => {
      const result = spanTextToSelectionsOrError(MOCK_PARTITIONS, '2022-01-01');
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01']);
      expect(result.selectedRanges).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 0, key: '2022-01-01'},
        },
      ]);
    });
    it('should parse comma-separated values', () => {
      const result = spanTextToSelectionsOrError(
        MOCK_PARTITIONS,
        '2022-01-01, 2022-01-02,2022-01-03',
      );
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01', '2022-01-02', '2022-01-03']);
      expect(result.selectedRanges).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 0, key: '2022-01-01'},
        },
        {
          start: {idx: 1, key: '2022-01-02'},
          end: {idx: 1, key: '2022-01-02'},
        },
        {
          start: {idx: 2, key: '2022-01-03'},
          end: {idx: 2, key: '2022-01-03'},
        },
      ]);
    });
    it('should parse spans using the [...] syntax', () => {
      const result = spanTextToSelectionsOrError(MOCK_PARTITIONS, '[2022-01-01...2022-01-03]');
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual(['2022-01-01', '2022-01-02', '2022-01-03']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 2, key: '2022-01-03'}},
      ]);
    });
    it('should parse a multi-span string', () => {
      const result = spanTextToSelectionsOrError(
        MOCK_PARTITIONS,
        '[2022-01-01...2022-01-03],2022-01-05,[2022-01-06...2022-01-07]',
      );
      if (result instanceof Error) {
        throw result;
      }
      expect(result.selectedKeys).toEqual([
        '2022-01-01',
        '2022-01-02',
        '2022-01-03',
        '2022-01-05',
        '2022-01-06',
        '2022-01-07',
      ]);
      expect(result.selectedRanges).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 2, key: '2022-01-03'},
        },
        {
          start: {idx: 4, key: '2022-01-05'},
          end: {idx: 4, key: '2022-01-05'},
        },
        {
          start: {idx: 5, key: '2022-01-06'},
          end: {idx: 6, key: '2022-01-07'},
        },
      ]);
    });
    it('should throw an exception if the string is invalid', () => {
      expect(spanTextToSelectionsOrError(MOCK_PARTITIONS, '[1980-01-01]') instanceof Error).toEqual(
        true,
      );
    });
  });

  describe('partitionsToText', () => {
    describe('without allKeys context', () => {
      it('serializes empty selection', () => {
        expect(partitionsToText([])).toBe('');
      });

      it('serializes single key', () => {
        expect(partitionsToText(['key1'])).toBe('key1');
      });

      it('serializes multiple keys', () => {
        expect(partitionsToText(['key1', 'key2', 'key3'])).toBe('key1, key2, key3');
      });

      it('escapes keys with special characters', () => {
        expect(partitionsToText(['normal', 'has,comma', 'another'])).toBe(
          'normal, "has,comma", another',
        );
      });

      it('handles all keys requiring escaping', () => {
        expect(partitionsToText(['a,b', '[c]', 'd*e'])).toBe('"a,b", "[c]", "d*e"');
      });
    });

    describe('with allKeys context (range optimization)', () => {
      const allKeys = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'];

      it('serializes empty selection', () => {
        expect(partitionsToText([], allKeys)).toBe('');
      });

      it('serializes single key', () => {
        expect(partitionsToText(['2024-01-01'], allKeys)).toBe('2024-01-01');
      });

      it('serializes two consecutive keys as range', () => {
        expect(partitionsToText(['2024-01-01', '2024-01-02'], allKeys)).toBe(
          '[2024-01-01...2024-01-02]',
        );
      });

      it('serializes three consecutive keys as range', () => {
        expect(partitionsToText(['2024-01-01', '2024-01-02', '2024-01-03'], allKeys)).toBe(
          '[2024-01-01...2024-01-03]',
        );
      });

      it('serializes all keys as full range', () => {
        expect(
          partitionsToText(
            ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            allKeys,
          ),
        ).toBe('[2024-01-01...2024-01-05]');
      });

      it('serializes non-consecutive keys as separate items', () => {
        expect(partitionsToText(['2024-01-01', '2024-01-03', '2024-01-05'], allKeys)).toBe(
          '2024-01-01, 2024-01-03, 2024-01-05',
        );
      });

      it('serializes mixed consecutive and non-consecutive', () => {
        expect(partitionsToText(['2024-01-01', '2024-01-02', '2024-01-05'], allKeys)).toBe(
          '[2024-01-01...2024-01-02], 2024-01-05',
        );
      });

      it('serializes multiple ranges', () => {
        expect(
          partitionsToText(['2024-01-01', '2024-01-02', '2024-01-04', '2024-01-05'], allKeys),
        ).toBe('[2024-01-01...2024-01-02], [2024-01-04...2024-01-05]');
      });

      it('handles keys not in allKeys (ignores them)', () => {
        expect(partitionsToText(['2024-01-01', 'unknown', '2024-01-02'], allKeys)).toBe(
          '[2024-01-01...2024-01-02]',
        );
      });

      it('handles empty allKeys array', () => {
        expect(partitionsToText(['key1', 'key2'], [])).toBe('key1, key2');
      });
    });

    describe('with special characters and allKeys context', () => {
      const allKeys = ['normal', 'has,comma', '[bracketed]', 'another'];

      it('escapes special characters in single keys', () => {
        expect(partitionsToText(['has,comma'], allKeys)).toBe('"has,comma"');
      });

      it('escapes special characters in ranges', () => {
        expect(partitionsToText(['has,comma', '[bracketed]'], allKeys)).toBe(
          '["has,comma"..."[bracketed]"]',
        );
      });

      it('mixes escaped and unescaped in output', () => {
        expect(partitionsToText(['normal', 'has,comma'], allKeys)).toBe('[normal..."has,comma"]');
      });
    });

    describe('edge cases', () => {
      it('handles single item in allKeys', () => {
        expect(partitionsToText(['only'], ['only'])).toBe('only');
      });

      it('handles selection order not matching allKeys order', () => {
        const allKeys = ['a', 'b', 'c'];
        // Selection in different order - should still produce correct range
        expect(partitionsToText(['c', 'a', 'b'], allKeys)).toBe('[a...c]');
      });

      it('handles duplicate keys in selection', () => {
        const allKeys = ['a', 'b', 'c'];
        expect(partitionsToText(['a', 'a', 'b'], allKeys)).toBe('[a...b]');
      });
    });

    describe('legacy tests', () => {
      it('should correctly build single partition lists', () => {
        expect(partitionsToText(['2022-01-01', '2022-01-07'], MOCK_PARTITIONS)).toEqual(
          '2022-01-01, 2022-01-07',
        );
      });

      it('should correctly build spans', () => {
        expect(
          partitionsToText(
            ['2022-01-01', '2022-01-02', '2022-01-03', '2022-01-05', '2022-01-06', '2022-01-07'],
            MOCK_PARTITIONS,
          ),
        ).toEqual('[2022-01-01...2022-01-03], [2022-01-05...2022-01-07]');
      });

      it('should ignore unknown partition keys, so the result string is always a valid selection', () => {
        expect(partitionsToText(['XXX', '2022-01-02'], MOCK_PARTITIONS)).toEqual('2022-01-02');
      });
    });
  });

  describe('special character handling', () => {
    describe('round-trip with quoted keys', () => {
      it('handles commas in partition keys', () => {
        const allKeys = ['normal', 'has,comma', 'another'];
        const selected = ['has,comma'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('"has,comma"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['has,comma']);
        }
      });

      it('handles brackets in partition keys', () => {
        const allKeys = ['normal', '[bracketed]', 'another'];
        const selected = ['[bracketed]'];

        const text = partitionsToText(selected, allKeys);
        const parsed = spanTextToSelectionsOrError(allKeys, text);

        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['[bracketed]']);
        }
      });

      it('handles quotes in partition keys', () => {
        const allKeys = ['normal', 'has"quote', 'another'];
        const selected = ['has"quote'];

        const text = partitionsToText(selected, allKeys);
        const parsed = spanTextToSelectionsOrError(allKeys, text);

        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['has"quote']);
        }
      });

      it('handles asterisks in partition keys', () => {
        const allKeys = ['normal', 'file*.txt', 'another'];
        const selected = ['file*.txt'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('"file*.txt"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['file*.txt']);
        }
      });

      it('handles ellipsis in partition keys', () => {
        const allKeys = ['normal', 'data...backup', 'another'];
        const selected = ['data...backup'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('"data...backup"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['data...backup']);
        }
      });

      it('handles dots in partition keys (must be quoted)', () => {
        const allKeys = ['normal', 'key.with.dots', 'another'];
        const selected = ['key.with.dots'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('"key.with.dots"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['key.with.dots']);
        }
      });

      it('handles backslashes in partition keys', () => {
        const allKeys = ['normal', 'path\\to\\file', 'another'];
        const selected = ['path\\to\\file'];

        const text = partitionsToText(selected, allKeys);
        // Should escape backslashes and wrap in quotes
        expect(text).toBe('"path\\\\to\\\\file"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['path\\to\\file']);
        }
      });
    });

    describe('ranges with special character keys', () => {
      it('handles range with comma in keys', () => {
        const allKeys = ['start,key', 'middle,key', 'end,key'];
        const selected = ['start,key', 'middle,key', 'end,key'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('["start,key"..."end,key"]');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['start,key', 'middle,key', 'end,key']);
        }
      });

      it('handles range with mixed special and normal keys', () => {
        const allKeys = ['normal-start', 'has,comma', 'normal-end'];
        const selected = ['normal-start', 'has,comma', 'normal-end'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('[normal-start...normal-end]');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['normal-start', 'has,comma', 'normal-end']);
        }
      });
    });

    describe('mixed selections with special characters', () => {
      it('handles non-consecutive keys with special characters', () => {
        const allKeys = ['first,key', 'second-key', 'third,key', 'fourth-key'];
        const selected = ['first,key', 'third,key'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('"first,key", "third,key"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['first,key', 'third,key']);
        }
      });

      it('handles complex mixed selection', () => {
        const allKeys = ['2024-01-01', 'data,file', '2024-01-02', '[special]', '2024-01-03'];
        const selected = ['2024-01-01', 'data,file', '2024-01-02'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('[2024-01-01...2024-01-02]');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['2024-01-01', 'data,file', '2024-01-02']);
        }
      });
    });

    describe('edge cases', () => {
      it('handles single key that needs escaping', () => {
        const allKeys = ['only,one'];
        const selected = ['only,one'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('"only,one"');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['only,one']);
        }
      });

      it('handles all keys having special characters', () => {
        const allKeys = ['[a]', '[b]', '[c]'];
        const selected = ['[a]', '[b]', '[c]'];

        const text = partitionsToText(selected, allKeys);
        expect(text).toBe('["[a]"..."[c]"]');

        const parsed = spanTextToSelectionsOrError(allKeys, text);
        expect(parsed).not.toBeInstanceOf(Error);
        if (!(parsed instanceof Error)) {
          expect(parsed.selectedKeys).toEqual(['[a]', '[b]', '[c]']);
        }
      });
    });
  });
});
