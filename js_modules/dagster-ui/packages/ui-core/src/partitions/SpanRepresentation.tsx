import {
  PartitionDimensionSelection,
  PartitionDimensionSelectionRange,
} from '../assets/usePartitionHealthData';

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

export function stringForSpan(
  {startIdx, endIdx}: {startIdx: number; endIdx: number},
  all: string[],
) {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return startIdx === endIdx ? all[startIdx]! : `[${all[startIdx]!}...${all[endIdx]!}]`;
}

export function allPartitionsSpan({partitionKeys}: {partitionKeys: string[]}) {
  return stringForSpan({startIdx: 0, endIdx: partitionKeys.length - 1}, partitionKeys);
}

export function allPartitionsRange({
  partitionKeys,
}: {
  partitionKeys: string[];
}): PartitionDimensionSelectionRange {
  return {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    start: {idx: 0, key: partitionKeys[0]!},
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    end: {idx: partitionKeys.length - 1, key: partitionKeys[partitionKeys.length - 1]!},
  };
}

// Intermediate representation for parsed span text
type ParsedSpanTerm =
  | {type: 'range'; start: string; end: string}
  | {type: 'wildcard'; prefix: string; suffix: string}
  | {type: 'single'; key: string};

/**
 * Parses span text into an intermediate representation of terms
 */
export function parseSpanText(text: string): ParsedSpanTerm[] {
  const terms = text.split(',').map((s) => s.trim());
  const parsedTerms: ParsedSpanTerm[] = [];

  for (const term of terms) {
    if (term.length === 0) {
      continue;
    }
    const rangeMatch = /^\[(.*)\.\.\.(.*)\]$/g.exec(term);
    if (rangeMatch) {
      const [, start, end] = rangeMatch;
      if (start !== undefined && end !== undefined) {
        parsedTerms.push({type: 'range', start, end});
      }
    } else if (term.includes('*')) {
      const [prefix, suffix] = term.split('*');
      parsedTerms.push({type: 'wildcard', prefix: prefix ?? '', suffix: suffix ?? ''});
    } else {
      parsedTerms.push({type: 'single', key: term});
    }
  }

  return parsedTerms;
}

/**
 * Converts parsed span terms into the final partition selection object
 */
export function convertToPartitionSelection(
  parsedTerms: ParsedSpanTerm[],
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
      result.selectedRanges.push({
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        start: {idx: allStartIdx, key: allPartitionKeys[allStartIdx]!},
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        end: {idx: allEndIdx, key: allPartitionKeys[allEndIdx]!},
      });
    } else if (term.type === 'wildcard') {
      let start = -1;
      const close = (end: number) => {
        result.selectedKeys = result.selectedKeys.concat(allPartitionKeys.slice(start, end + 1));
        result.selectedRanges.push({
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          start: {idx: start, key: allPartitionKeys[start]!},
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          end: {idx: end, key: allPartitionKeys[end]!},
        });
        start = -1;
      };

      // todo bengotow: Was this change correct??
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

export function spanTextToSelectionsOrError(
  allPartitionKeys: string[],
  text: string,
  skipPartitionKeyValidation?: boolean, // This is used by Dynamic Partitions as a workaround to be able to select a newly added partition before the partition health data is refetched
): Error | Omit<PartitionDimensionSelection, 'dimension'> {
  const parsedTerms = parseSpanText(text);
  return convertToPartitionSelection(parsedTerms, allPartitionKeys, skipPartitionKeyValidation);
}

export function partitionsToText(selected: string[], all?: string[]) {
  if (selected.length === all?.length) {
    return allPartitionsSpan({partitionKeys: all});
  }
  const selectedSet = new Set(selected);
  if (!all) {
    return Array.from(selectedSet).join(', ');
  }
  return assembleIntoSpans(all, (key) => selectedSet.has(key))
    .filter((s) => s.status)
    .map((s) => stringForSpan(s, all))
    .join(', ');
}
