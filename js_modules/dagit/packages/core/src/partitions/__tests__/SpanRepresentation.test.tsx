import {
  allPartitionsSpan,
  assembleIntoSpans,
  partitionsToText,
  stringForSpan,
  spanTextToSelections,
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

  describe('textToPartitions', () => {
    it('should parse a single value', () => {
      const result = spanTextToSelections(MOCK_PARTITIONS, '2022-01-01');
      expect(result.selectedKeys).toEqual(['2022-01-01']);
      expect(result.selectedRanges).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 0, key: '2022-01-01'},
        },
      ]);
    });
    it('should parse comma-separated values', () => {
      const result = spanTextToSelections(MOCK_PARTITIONS, '2022-01-01, 2022-01-02,2022-01-03');

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
      const result = spanTextToSelections(MOCK_PARTITIONS, '[2022-01-01...2022-01-03]');
      expect(result.selectedKeys).toEqual(['2022-01-01', '2022-01-02', '2022-01-03']);
      expect(result.selectedRanges).toEqual([
        {start: {idx: 0, key: '2022-01-01'}, end: {idx: 2, key: '2022-01-03'}},
      ]);
    });
    it('should parse a multi-span string', () => {
      const result = spanTextToSelections(
        MOCK_PARTITIONS,
        '[2022-01-01...2022-01-03],2022-01-05,[2022-01-06...2022-01-07]',
      );
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
      expect(() => spanTextToSelections(MOCK_PARTITIONS, '[1980-01-01]')).toThrow();
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
