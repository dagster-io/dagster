import {
  allPartitionsSpan,
  assembleIntoSpans,
  convertToPartitionSelection,
  parseSpanText,
  partitionsToText,
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
