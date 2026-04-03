import {useCallback, useEffect, useRef} from 'react';

import {GraphData, groupIdForNode} from './Utils';
import {IPoint} from '../graph/common';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

function validateOverrides(json: any): Record<string, IPoint> {
  if (json && typeof json === 'object' && !Array.isArray(json)) {
    const result: Record<string, IPoint> = {};
    for (const [key, value] of Object.entries(json)) {
      if (
        value &&
        typeof value === 'object' &&
        typeof (value as any).x === 'number' &&
        typeof (value as any).y === 'number'
      ) {
        result[key] = {x: (value as any).x, y: (value as any).y};
      }
    }
    return result;
  }
  return {};
}

export function usePositionOverrides(
  storageKey: string,
  graphData: GraphData,
  pruneGraphData: GraphData = graphData,
) {
  const [overrides, setOverrides, clearOverrides] = useStateWithStorage(
    storageKey,
    validateOverrides,
  );

  // Keep a ref so the pruning effect can read overrides without adding it to deps.
  // Without this, calling setOverrides inside the effect would re-trigger it on every
  // override change (one extra render per drag commit), making the dep cycle fragile.
  const overridesRef = useRef(overrides);
  overridesRef.current = overrides;

  // Prune overrides for nodes and groups no longer in the graph.
  useEffect(() => {
    const nodeIds = Object.keys(pruneGraphData.nodes);
    const groupIds = new Set<string>();
    Object.values(pruneGraphData.nodes).forEach((node) => {
      if (node.definition.groupName) {
        groupIds.add(groupIdForNode(node));
      }
    });

    const currentIds = new Set([...nodeIds, ...groupIds]);
    const stale = Object.keys(overridesRef.current).filter((id) => !currentIds.has(id));

    if (stale.length === 0) {
      return;
    }
    setOverrides((prev) => {
      const pruned = {...prev};
      stale.forEach((id) => delete pruned[id]);
      return pruned;
    });
  }, [pruneGraphData.nodes, setOverrides]);

  const updateNodePosition = useCallback(
    (nodeId: string, position: IPoint) => {
      const clamped: IPoint = {x: Math.max(0, position.x), y: Math.max(0, position.y)};
      setOverrides((prev) => ({...prev, [nodeId]: clamped}));
    },
    [setOverrides],
  );

  const updateMultiplePositions = useCallback(
    (updates: Record<string, IPoint>) => {
      const clamped: Record<string, IPoint> = {};
      for (const [id, pos] of Object.entries(updates)) {
        clamped[id] = {x: Math.max(0, pos.x), y: Math.max(0, pos.y)};
      }
      setOverrides((prev) => ({...prev, ...clamped}));
    },
    [setOverrides],
  );

  const resetNodePosition = useCallback(
    (nodeId: string) => {
      setOverrides((prev) => {
        const next = {...prev};
        delete next[nodeId];
        return next;
      });
    },
    [setOverrides],
  );

  const resetMultiplePositions = useCallback(
    (ids: string[]) => {
      setOverrides((prev) => {
        const next = {...prev};
        ids.forEach((id) => delete next[id]);
        return next;
      });
    },
    [setOverrides],
  );

  const hasOverrides = Object.keys(overrides).length > 0;

  return {
    overrides,
    updateNodePosition,
    updateMultiplePositions,
    resetNodePosition,
    resetMultiplePositions,
    resetAllOverrides: clearOverrides,
    hasOverrides,
  };
}
