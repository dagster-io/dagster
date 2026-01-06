/**
 * Regular expression matching characters that require quoting in partition keys.
 * These characters have special meaning in the partition selection syntax:
 * - , (comma): separates partition items
 * - [ ] (brackets): range delimiters
 * - . (dot): part of range delimiter ...
 * - * (asterisk): wildcard character
 * - " (quote): string delimiter
 * - \ (backslash): escape character
 */
const SPECIAL_CHARS = /[,[\].*"\\]/;

/**
 * Escape a partition key for serialization.
 * Keys containing special characters are wrapped in quotes with proper escaping.
 *
 * @param key The partition key to escape
 * @returns The escaped key, quoted if necessary
 *
 * @example
 * escapePartitionKey('simple-key')
 * // => 'simple-key'
 *
 * @example
 * escapePartitionKey('key,with,commas')
 * // => '"key,with,commas"'
 *
 * @example
 * escapePartitionKey('key"with"quotes')
 * // => '"key\\"with\\"quotes"'
 */
export function escapePartitionKey(key: string): string {
  if (!SPECIAL_CHARS.test(key)) {
    return key;
  }
  // Escape backslashes first (so we don't double-escape), then quotes
  const escaped = key.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  return `"${escaped}"`;
}

/**
 * Serialize a range to string format: [start...end]
 *
 * @param start The start partition key
 * @param end The end partition key
 * @returns The serialized range string
 *
 * @example
 * serializeRange('2024-01-01', '2024-12-31')
 * // => '[2024-01-01...2024-12-31]'
 *
 * @example
 * serializeRange('key,start', 'key,end')
 * // => '["key,start"..."key,end"]'
 */
export function serializeRange(start: string, end: string): string {
  return `[${escapePartitionKey(start)}...${escapePartitionKey(end)}]`;
}

/**
 * Assemble selected keys into contiguous spans for range optimization.
 * This finds consecutive sequences of selected keys in the allKeys array.
 *
 * @param allKeys All available partition keys in order
 * @param selectedKeys The keys that are selected
 * @returns Array of spans with start and end indices into allKeys
 */
function assembleIntoSpans(
  allKeys: string[],
  selectedKeys: string[],
): Array<{startIdx: number; endIdx: number}> {
  const selectedSet = new Set(selectedKeys);
  const spans: Array<{startIdx: number; endIdx: number}> = [];

  let currentSpan: {startIdx: number; endIdx: number} | null = null;

  allKeys.forEach((key, idx) => {
    if (selectedSet.has(key)) {
      if (currentSpan === null) {
        currentSpan = {startIdx: idx, endIdx: idx};
      } else {
        currentSpan.endIdx = idx;
      }
    } else {
      if (currentSpan !== null) {
        spans.push(currentSpan);
        currentSpan = null;
      }
    }
  });

  if (currentSpan !== null) {
    spans.push(currentSpan);
  }

  return spans;
}

/**
 * Serialize selected partitions to a text representation.
 * When allKeys is provided, optimizes for readability by using ranges
 * for consecutive keys.
 *
 * @param selectedKeys The selected partition keys
 * @param allKeys All available partition keys (for determining ranges)
 * @returns Serialized string representation
 *
 * @example
 * // Without allKeys - just escapes and joins
 * serializePartitionSelection(['key1', 'key2'])
 * // => 'key1, key2'
 *
 * @example
 * // With allKeys - consecutive keys become ranges
 * const allKeys = ['2024-01', '2024-02', '2024-03', '2024-04'];
 * serializePartitionSelection(['2024-01', '2024-02', '2024-03'], allKeys)
 * // => '[2024-01...2024-03]'
 *
 * @example
 * // Mixed selection
 * const allKeys = ['a', 'b', 'c', 'd', 'e'];
 * serializePartitionSelection(['a', 'b', 'e'], allKeys)
 * // => '[a...b], e'
 */
export function serializePartitionSelection(selectedKeys: string[], allKeys?: string[]): string {
  if (selectedKeys.length === 0) {
    return '';
  }

  // If we have allKeys, try to optimize into ranges
  if (allKeys && allKeys.length > 0) {
    const spans = assembleIntoSpans(allKeys, selectedKeys);
    return spans
      .map((span) => {
        const startKey = allKeys[span.startIdx];
        const endKey = allKeys[span.endIdx];
        if (!startKey || !endKey) {
          return '';
        }
        if (span.startIdx === span.endIdx) {
          return escapePartitionKey(startKey);
        }
        return serializeRange(startKey, endKey);
      })
      .filter(Boolean)
      .join(', ');
  }

  // Without allKeys, just escape and join
  return selectedKeys.map(escapePartitionKey).join(', ');
}
