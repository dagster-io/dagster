import {
  escapePartitionKey,
  serializePartitionSelection,
  serializeRange,
} from '../serializePartitionSelection';

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
    expect(serializeRange('start...value', 'end...value')).toBe('["start...value"..."end...value"]');
  });
});

describe('serializePartitionSelection', () => {
  describe('without allKeys context', () => {
    it('serializes empty selection', () => {
      expect(serializePartitionSelection([])).toBe('');
    });

    it('serializes single key', () => {
      expect(serializePartitionSelection(['key1'])).toBe('key1');
    });

    it('serializes multiple keys', () => {
      expect(serializePartitionSelection(['key1', 'key2', 'key3'])).toBe('key1, key2, key3');
    });

    it('escapes keys with special characters', () => {
      expect(serializePartitionSelection(['normal', 'has,comma', 'another'])).toBe(
        'normal, "has,comma", another',
      );
    });

    it('handles all keys requiring escaping', () => {
      expect(serializePartitionSelection(['a,b', '[c]', 'd*e'])).toBe('"a,b", "[c]", "d*e"');
    });
  });

  describe('with allKeys context (range optimization)', () => {
    const allKeys = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'];

    it('serializes empty selection', () => {
      expect(serializePartitionSelection([], allKeys)).toBe('');
    });

    it('serializes single key', () => {
      expect(serializePartitionSelection(['2024-01-01'], allKeys)).toBe('2024-01-01');
    });

    it('serializes two consecutive keys as range', () => {
      expect(serializePartitionSelection(['2024-01-01', '2024-01-02'], allKeys)).toBe(
        '[2024-01-01...2024-01-02]',
      );
    });

    it('serializes three consecutive keys as range', () => {
      expect(serializePartitionSelection(['2024-01-01', '2024-01-02', '2024-01-03'], allKeys)).toBe(
        '[2024-01-01...2024-01-03]',
      );
    });

    it('serializes all keys as full range', () => {
      expect(
        serializePartitionSelection(
          ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
          allKeys,
        ),
      ).toBe('[2024-01-01...2024-01-05]');
    });

    it('serializes non-consecutive keys as separate items', () => {
      expect(serializePartitionSelection(['2024-01-01', '2024-01-03', '2024-01-05'], allKeys)).toBe(
        '2024-01-01, 2024-01-03, 2024-01-05',
      );
    });

    it('serializes mixed consecutive and non-consecutive', () => {
      expect(
        serializePartitionSelection(['2024-01-01', '2024-01-02', '2024-01-05'], allKeys),
      ).toBe('[2024-01-01...2024-01-02], 2024-01-05');
    });

    it('serializes multiple ranges', () => {
      expect(
        serializePartitionSelection(
          ['2024-01-01', '2024-01-02', '2024-01-04', '2024-01-05'],
          allKeys,
        ),
      ).toBe('[2024-01-01...2024-01-02], [2024-01-04...2024-01-05]');
    });

    it('handles keys not in allKeys (ignores them)', () => {
      expect(serializePartitionSelection(['2024-01-01', 'unknown', '2024-01-02'], allKeys)).toBe(
        '[2024-01-01...2024-01-02]',
      );
    });

    it('handles empty allKeys array', () => {
      expect(serializePartitionSelection(['key1', 'key2'], [])).toBe('key1, key2');
    });
  });

  describe('with special characters and allKeys context', () => {
    const allKeys = ['normal', 'has,comma', '[bracketed]', 'another'];

    it('escapes special characters in single keys', () => {
      expect(serializePartitionSelection(['has,comma'], allKeys)).toBe('"has,comma"');
    });

    it('escapes special characters in ranges', () => {
      expect(serializePartitionSelection(['has,comma', '[bracketed]'], allKeys)).toBe(
        '["has,comma"..."[bracketed]"]',
      );
    });

    it('mixes escaped and unescaped in output', () => {
      expect(serializePartitionSelection(['normal', 'has,comma'], allKeys)).toBe(
        '[normal..."has,comma"]',
      );
    });
  });

  describe('edge cases', () => {
    it('handles single item in allKeys', () => {
      expect(serializePartitionSelection(['only'], ['only'])).toBe('only');
    });

    it('handles selection order not matching allKeys order', () => {
      const allKeys = ['a', 'b', 'c'];
      // Selection in different order - should still produce correct range
      expect(serializePartitionSelection(['c', 'a', 'b'], allKeys)).toBe('[a...c]');
    });

    it('handles duplicate keys in selection', () => {
      const allKeys = ['a', 'b', 'c'];
      expect(serializePartitionSelection(['a', 'a', 'b'], allKeys)).toBe('[a...b]');
    });
  });
});
