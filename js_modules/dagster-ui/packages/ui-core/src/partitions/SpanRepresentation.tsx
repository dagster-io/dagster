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
    start: {idx: 0, key: partitionKeys[0]!},
    end: {idx: partitionKeys.length - 1, key: partitionKeys[partitionKeys.length - 1]!},
  };
}

export function spanTextToSelectionsOrError(
  allPartitionKeys: string[],
  text: string,
  skipPartitionKeyValidation?: boolean, // This is used by Dynamic Partitions as a workaround to be able to select a newly added partition before the partition health data is refetched
): Error | Omit<PartitionDimensionSelection, 'dimension'> {
  const terms = text.split(',').map((s) => s.trim());
  const result: Omit<PartitionDimensionSelection, 'dimension'> = {
    selectedKeys: [],
    selectedRanges: [],
  };

  for (const term of terms) {
    if (term.length === 0) {
      continue;
    }
    const rangeMatch = /^\[(.*)\.\.\.(.*)\]$/g.exec(term);
    if (rangeMatch) {
      const [, start, end] = rangeMatch;
      const allStartIdx = allPartitionKeys.indexOf(start!);
      const allEndIdx = allPartitionKeys.indexOf(end!);
      if (allStartIdx === -1 || allEndIdx === -1) {
        return new Error(`Could not find partitions for provided range: ${start}...${end}`);
      }
      result.selectedKeys = result.selectedKeys.concat(
        allPartitionKeys.slice(allStartIdx, allEndIdx + 1),
      );
      result.selectedRanges.push({
        start: {idx: allStartIdx, key: allPartitionKeys[allStartIdx]!},
        end: {idx: allEndIdx, key: allPartitionKeys[allEndIdx]!},
      });
    } else if (term.includes('*')) {
      const [prefix, suffix] = term.split('*');

      let start = -1;
      const close = (end: number) => {
        result.selectedKeys = result.selectedKeys.concat(allPartitionKeys.slice(start, end + 1));
        result.selectedRanges.push({
          start: {idx: start, key: allPartitionKeys[start]!},
          end: {idx: end, key: allPartitionKeys[end]!},
        });
        start = -1;
      };

      // todo bengotow: Was this change correct??
      allPartitionKeys.forEach((key, idx) => {
        const match = key.startsWith(prefix!) && key.endsWith(suffix!);
        if (match && start === -1) {
          start = idx;
        }
        if (!match && start !== -1) {
          close(idx);
        }
      });

      if (start !== -1) {
        close(allPartitionKeys.length - 1);
      }
    } else {
      const idx = allPartitionKeys.indexOf(term);
      if (idx === -1 && !skipPartitionKeyValidation) {
        return new Error(`Could not find partition: ${term}`);
      }
      result.selectedKeys.push(term);
      result.selectedRanges.push({
        start: {idx, key: term},
        end: {idx, key: term},
      });
    }
  }

  result.selectedKeys = Array.from(new Set(result.selectedKeys));

  return result;
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
