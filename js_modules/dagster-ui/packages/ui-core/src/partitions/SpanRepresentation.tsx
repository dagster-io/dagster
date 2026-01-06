import {ParsedPartitionTerm} from './AntlrPartitionSelectionVisitor';
import {parsePartitionSelection} from './parsePartitionSelection';
import {
  escapePartitionKey,
  serializePartitionSelection,
  serializeRange,
} from './serializePartitionSelection';
import {
  PartitionDimensionSelection,
  PartitionDimensionSelectionRange,
} from '../assets/usePartitionHealthData';

// Re-export ParsedPartitionTerm as ParsedSpanTerm for backward compatibility
export type {ParsedPartitionTerm as ParsedSpanTerm} from './AntlrPartitionSelectionVisitor';

/**
 * Assembles partition keys into contiguous spans based on a test function.
 * This is a generic utility used for partition status visualization and other purposes.
 *
 * @param keys All partition keys in order
 * @param keyTestFn Function that returns a status value for each key
 * @returns Array of spans with start/end indices and status
 */
export function assembleIntoSpans<T>(keys: string[], keyTestFn: (key: string, idx: number) => T) {
  const spans: {startIdx: number; endIdx: number; status: T}[] = [];

  keys.forEach((key, ii) => {
    const status = keyTestFn(key, ii);
    const lastSpan = spans[spans.length - 1];
    if (!lastSpan || lastSpan.status !== status) {
      spans.push({startIdx: ii, endIdx: ii, status});
    } else {
      lastSpan.endIdx = ii;
    }
  });

  return spans;
}

/**
 * Converts a span (start/end indices) to a string representation.
 * Uses proper escaping for partition keys that contain special characters.
 *
 * @param span The span with startIdx and endIdx
 * @param all All partition keys (to look up the actual key strings)
 * @returns String representation (single key or [start...end] range)
 */
export function stringForSpan(
  {startIdx, endIdx}: {startIdx: number; endIdx: number},
  all: string[],
): string {
  const startKey = all[startIdx];
  const endKey = all[endIdx];

  if (!startKey || !endKey) {
    return '';
  }

  if (startIdx === endIdx) {
    return escapePartitionKey(startKey);
  }

  return serializeRange(startKey, endKey);
}

/**
 * Returns the string representation of selecting all partitions.
 *
 * @param partitionKeys All partition keys
 * @returns String like "[first...last]"
 */
export function allPartitionsSpan({partitionKeys}: {partitionKeys: string[]}): string {
  const firstKey = partitionKeys[0];
  const lastKey = partitionKeys[partitionKeys.length - 1];

  if (!firstKey || !lastKey) {
    return '';
  }

  if (partitionKeys.length === 1) {
    return escapePartitionKey(firstKey);
  }

  return serializeRange(firstKey, lastKey);
}

/**
 * Creates a PartitionDimensionSelectionRange representing all partitions.
 *
 * @param partitionKeys All partition keys
 * @returns Range from first to last partition
 */
export function allPartitionsRange({
  partitionKeys,
}: {
  partitionKeys: string[];
}): PartitionDimensionSelectionRange {
  const firstKey = partitionKeys[0];
  const lastKey = partitionKeys[partitionKeys.length - 1];

  return {
    start: {idx: 0, key: firstKey ?? ''},
    end: {idx: partitionKeys.length - 1, key: lastKey ?? ''},
  };
}

/**
 * Parses span text into an intermediate representation of terms.
 * Uses the ANTLR-based parser for proper handling of special characters.
 *
 * @deprecated Use parsePartitionSelection directly for new code
 * @param text The span text to parse
 * @returns Array of parsed terms
 */
export function parseSpanText(text: string): ParsedPartitionTerm[] {
  const result = parsePartitionSelection(text);
  if (result instanceof Error) {
    // Return empty array on parse error for backward compatibility
    return [];
  }
  return result;
}

/**
 * Converts parsed span terms into the final partition selection object.
 *
 * @param parsedTerms Parsed terms from parseSpanText or parsePartitionSelection
 * @param allPartitionKeys All available partition keys
 * @param skipPartitionKeyValidation Skip validation for dynamic partitions
 * @returns Selection object or Error
 */
export function convertToPartitionSelection(
  parsedTerms: ParsedPartitionTerm[],
  allPartitionKeys: string[],
  skipPartitionKeyValidation?: boolean,
): Error | Omit<PartitionDimensionSelection, 'dimension'> {
  const result: Omit<PartitionDimensionSelection, 'dimension'> = {
    selectedKeys: [],
    selectedRanges: [],
  };

  for (const term of parsedTerms) {
    if (term.type === 'range') {
      const allStartIdx = allPartitionKeys.indexOf(term.start);
      const allEndIdx = allPartitionKeys.indexOf(term.end);
      if (allStartIdx === -1 || allEndIdx === -1) {
        return new Error(
          `Could not find partitions for provided range: ${term.start}...${term.end}`,
        );
      }
      result.selectedKeys = result.selectedKeys.concat(
        allPartitionKeys.slice(allStartIdx, allEndIdx + 1),
      );
      const startKey = allPartitionKeys[allStartIdx];
      const endKey = allPartitionKeys[allEndIdx];
      if (startKey && endKey) {
        result.selectedRanges.push({
          start: {idx: allStartIdx, key: startKey},
          end: {idx: allEndIdx, key: endKey},
        });
      }
    } else if (term.type === 'wildcard') {
      let start = -1;
      const close = (end: number) => {
        result.selectedKeys = result.selectedKeys.concat(allPartitionKeys.slice(start, end + 1));
        const startKey = allPartitionKeys[start];
        const endKey = allPartitionKeys[end];
        if (startKey && endKey) {
          result.selectedRanges.push({
            start: {idx: start, key: startKey},
            end: {idx: end, key: endKey},
          });
        }
        start = -1;
      };

      allPartitionKeys.forEach((key, idx) => {
        const match = key.startsWith(term.prefix) && key.endsWith(term.suffix);
        if (match && start === -1) {
          start = idx;
        }
        if (!match && start !== -1) {
          close(idx - 1);
        }
      });

      if (start !== -1) {
        close(allPartitionKeys.length - 1);
      }
    } else if (term.type === 'single') {
      const idx = allPartitionKeys.indexOf(term.key);
      if (idx === -1 && !skipPartitionKeyValidation) {
        return new Error(`Could not find partition: ${term.key}`);
      }
      result.selectedKeys.push(term.key);
      result.selectedRanges.push({
        start: {idx, key: term.key},
        end: {idx, key: term.key},
      });
    }
  }

  result.selectedKeys = Array.from(new Set(result.selectedKeys));

  return result;
}

/**
 * Parse span text and convert to partition selection in one step.
 *
 * @param allPartitionKeys All available partition keys
 * @param text The span text to parse
 * @param skipPartitionKeyValidation Skip validation for dynamic partitions
 * @returns Selection object or Error
 */
export function spanTextToSelectionsOrError(
  allPartitionKeys: string[],
  text: string,
  skipPartitionKeyValidation?: boolean,
): Error | Omit<PartitionDimensionSelection, 'dimension'> {
  const parsedTerms = parsePartitionSelection(text);
  if (parsedTerms instanceof Error) {
    return parsedTerms;
  }
  return convertToPartitionSelection(parsedTerms, allPartitionKeys, skipPartitionKeyValidation);
}

/**
 * Convert selected partition keys to text representation.
 * Uses the new serialization functions with proper escaping.
 *
 * @param selected Selected partition keys
 * @param all All available partition keys (for range optimization)
 * @returns Text representation
 */
export function partitionsToText(selected: string[], all?: string[]): string {
  return serializePartitionSelection(selected, all);
}
