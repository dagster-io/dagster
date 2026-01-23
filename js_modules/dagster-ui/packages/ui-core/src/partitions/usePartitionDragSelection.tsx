import * as React from 'react';

import {assembleIntoSpans} from './SpanRepresentation';

type SelectionRange = {
  start: string;
  end: string;
};

interface UsePartitionDragSelectionParams {
  partitionKeys: string[];
  selected: string[] | undefined;
  onSelect: ((selected: string[]) => void) | undefined;
  containerRef: React.RefObject<HTMLDivElement>;
}

interface UsePartitionDragSelectionResult {
  currentSelectionRange: SelectionRange | undefined;
  selectedSet: Set<string>;
  selectedSpans: Array<{startIdx: number; endIdx: number; status: boolean}>;
  handleMouseDown: (e: React.MouseEvent) => void;
}

/**
 * Shared hook for partition drag selection logic.
 * Handles mouse drag selection with shift-key modifiers for add/subtract/replace operations.
 */
export function usePartitionDragSelection({
  partitionKeys,
  selected,
  onSelect,
  containerRef,
}: UsePartitionDragSelectionParams): UsePartitionDragSelectionResult {
  const [currentSelectionRange, setCurrentSelectionRange] = React.useState<
    SelectionRange | undefined
  >();

  const toPartitionName = React.useCallback(
    (e: MouseEvent) => {
      if (!containerRef.current) {
        return null;
      }
      const percentage =
        (e.clientX - containerRef.current.getBoundingClientRect().left) /
        containerRef.current.clientWidth;
      return partitionKeys[Math.floor(percentage * partitionKeys.length)];
    },
    [partitionKeys, containerRef],
  );

  const getRangeSelection = React.useCallback(
    (start: string, end: string) => {
      const startIdx = partitionKeys.indexOf(start);
      const endIdx = partitionKeys.indexOf(end);
      return partitionKeys.slice(Math.min(startIdx, endIdx), Math.max(startIdx, endIdx) + 1);
    },
    [partitionKeys],
  );

  const selectedSet = React.useMemo(() => new Set(selected), [selected]);

  // Handle drag selection
  React.useEffect(() => {
    if (!currentSelectionRange || !onSelect || !selected) {
      return;
    }
    const onMouseMove = (e: MouseEvent) => {
      const end = toPartitionName(e) || currentSelectionRange.end;
      setCurrentSelectionRange({start: currentSelectionRange?.start, end});
    };
    const onMouseUp = (e: MouseEvent) => {
      if (!currentSelectionRange) {
        return;
      }
      const end = toPartitionName(e) || currentSelectionRange.end;
      const currentSelection = getRangeSelection(currentSelectionRange.start, end);

      const operation = !e.getModifierState('Shift')
        ? 'replace'
        : currentSelection.every((name) => selectedSet.has(name))
          ? 'subtract'
          : 'add';

      if (operation === 'replace') {
        onSelect(currentSelection);
      } else if (operation === 'subtract') {
        onSelect(selected.filter((x) => !currentSelection.includes(x)));
      } else if (operation === 'add') {
        onSelect(Array.from(new Set([...selected, ...currentSelection])));
      }
      setCurrentSelectionRange(undefined);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [onSelect, selected, selectedSet, currentSelectionRange, getRangeSelection, toPartitionName]);

  const selectedSpans = React.useMemo(
    () =>
      selectedSet.size === 0
        ? []
        : selectedSet.size === partitionKeys.length
          ? [{startIdx: 0, endIdx: partitionKeys.length - 1, status: true}]
          : assembleIntoSpans(partitionKeys, (key) => selectedSet.has(key)).filter((s) => s.status),
    [selectedSet, partitionKeys],
  );

  const handleMouseDown = React.useCallback(
    (e: React.MouseEvent) => {
      if (!onSelect) {
        return;
      }
      const partitionName = toPartitionName(e.nativeEvent);
      if (partitionName) {
        setCurrentSelectionRange({start: partitionName, end: partitionName});
      }
    },
    [onSelect, toPartitionName],
  );

  return {
    currentSelectionRange,
    selectedSet,
    selectedSpans,
    handleMouseDown,
  };
}
