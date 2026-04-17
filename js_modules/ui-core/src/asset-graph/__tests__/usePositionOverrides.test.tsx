import {act, renderHook} from '@testing-library/react';

import {GraphData} from '../Utils';
import {usePositionOverrides} from '../usePositionOverrides';

const STORAGE_KEY = 'test-position-overrides';

/** Minimal GraphData with the given node IDs */
function makeGraphData(ids: string[]): GraphData {
  const nodes: GraphData['nodes'] = {};
  ids.forEach((id) => {
    nodes[id] = {
      id,
      assetKey: {path: JSON.parse(id), __typename: 'AssetKey'},
      definition: {} as any,
    };
  });
  return {nodes, downstream: {}, upstream: {}};
}

describe('usePositionOverrides', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('initial state', () => {
    it('returns empty overrides when localStorage is empty', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      expect(result.current.overrides).toEqual({});
      expect(result.current.hasOverrides).toBe(false);
    });

    it('loads persisted overrides from localStorage on mount', () => {
      const stored = {'["asset_a"]': {x: 50, y: 100}};
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));

      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      expect(result.current.overrides).toEqual(stored);
      expect(result.current.hasOverrides).toBe(true);
    });
  });

  describe('updateNodePosition', () => {
    it('adds a position override for a node', () => {
      const graphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 200, y: 300});
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 200, y: 300});
      expect(result.current.hasOverrides).toBe(true);
    });

    it('updates an existing override for the same node', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 100, y: 100});
      });
      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 999, y: 888});
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 999, y: 888});
    });

    it('persists the position to localStorage', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 42, y: 7});
      });

      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      expect(stored['["asset_a"]']).toEqual({x: 42, y: 7});
    });
  });

  describe('updateMultiplePositions', () => {
    it('adds multiple overrides at once', () => {
      const graphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateMultiplePositions({
          '["asset_a"]': {x: 10, y: 20},
          '["asset_b"]': {x: 30, y: 40},
        });
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 10, y: 20});
      expect(result.current.overrides['["asset_b"]']).toEqual({x: 30, y: 40});
    });

    it('merges with existing overrides', () => {
      const graphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 1, y: 2});
      });
      act(() => {
        result.current.updateMultiplePositions({'["asset_b"]': {x: 3, y: 4}});
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 1, y: 2});
      expect(result.current.overrides['["asset_b"]']).toEqual({x: 3, y: 4});
    });
  });

  describe('resetAllOverrides', () => {
    it('clears all overrides', () => {
      const graphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 10, y: 20});
        result.current.updateNodePosition('["asset_b"]', {x: 30, y: 40});
      });
      act(() => {
        result.current.resetAllOverrides();
      });

      expect(result.current.overrides).toEqual({});
      expect(result.current.hasOverrides).toBe(false);
    });

    it('removes the key from localStorage', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 10, y: 20});
      });
      act(() => {
        result.current.resetAllOverrides();
      });

      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
  });

  describe('resetMultiplePositions', () => {
    it('removes a group override and its child overrides together while preserving unrelated overrides', () => {
      const graphData = makeGraphData(['["asset_a"]', '["asset_b"]', '["asset_c"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateMultiplePositions({
          'group@repo:loc': {x: 10, y: 20},
          '["asset_a"]': {x: 30, y: 40},
          '["asset_b"]': {x: 50, y: 60},
          '["asset_c"]': {x: 70, y: 80},
        });
      });

      act(() => {
        result.current.resetMultiplePositions(['group@repo:loc', '["asset_a"]', '["asset_b"]']);
      });

      expect(result.current.overrides['group@repo:loc']).toBeUndefined();
      expect(result.current.overrides['["asset_a"]']).toBeUndefined();
      expect(result.current.overrides['["asset_b"]']).toBeUndefined();
      expect(result.current.overrides['["asset_c"]']).toEqual({x: 70, y: 80});
    });
  });

  describe('stale override pruning', () => {
    it('prunes overrides for nodes removed from the graph', () => {
      // Start with two nodes, one has an override
      const fullGraphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result, rerender} = renderHook(
        ({graphData}: {graphData: GraphData}) => usePositionOverrides(STORAGE_KEY, graphData),
        {initialProps: {graphData: fullGraphData}},
      );

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 100, y: 200});
        result.current.updateNodePosition('["asset_b"]', {x: 300, y: 400});
      });

      // Re-render with asset_b removed from graph
      const reducedGraphData = makeGraphData(['["asset_a"]']);
      rerender({graphData: reducedGraphData});

      // asset_b override should be pruned
      expect(result.current.overrides['["asset_b"]']).toBeUndefined();
      // asset_a override should remain
      expect(result.current.overrides['["asset_a"]']).toEqual({x: 100, y: 200});
    });

    it('does not prune overrides when the same graph is re-rendered', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result, rerender} = renderHook(
        ({graphData}: {graphData: GraphData}) => usePositionOverrides(STORAGE_KEY, graphData),
        {initialProps: {graphData}},
      );

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 50, y: 60});
      });

      // Rerender with the same graphData reference — no pruning should occur
      rerender({graphData});

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 50, y: 60});
    });

    it('does not prune overrides for nodes hidden by the current query', () => {
      const fullGraphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result, rerender} = renderHook(
        ({graphData, pruneGraphData}: {graphData: GraphData; pruneGraphData: GraphData}) =>
          usePositionOverrides(STORAGE_KEY, graphData, pruneGraphData),
        {initialProps: {graphData: fullGraphData, pruneGraphData: fullGraphData}},
      );

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 100, y: 200});
        result.current.updateNodePosition('["asset_b"]', {x: 300, y: 400});
      });

      rerender({
        graphData: makeGraphData(['["asset_a"]']),
        pruneGraphData: fullGraphData,
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 100, y: 200});
      expect(result.current.overrides['["asset_b"]']).toEqual({x: 300, y: 400});
    });
  });

  describe('group override pruning', () => {
    /** Creates nodes tagged with a groupName so the hook can register the group ID */
    function makeGraphDataWithGroup(nodeIds: string[], groupName: string): GraphData {
      const nodes: GraphData['nodes'] = {};
      nodeIds.forEach((id) => {
        nodes[id] = {
          id,
          assetKey: {path: JSON.parse(id), __typename: 'AssetKey'},
          definition: {
            groupName,
            repository: {name: 'global', location: {name: 'global'}, __typename: 'Repository'},
          } as any,
        };
      });
      return {nodes, downstream: {}, upstream: {}};
    }

    it('preserves group overrides when the group still exists in the graph', () => {
      const graphData = makeGraphDataWithGroup(['["asset_a"]'], 'mygroup');
      const {result, rerender} = renderHook(
        ({graphData}: {graphData: GraphData}) => usePositionOverrides(STORAGE_KEY, graphData),
        {initialProps: {graphData}},
      );

      // groupIdForNode emits "global@global:mygroup" when groupsPerCodeLocation flag is off
      act(() => {
        result.current.updateNodePosition('global@global:mygroup', {x: 100, y: 200});
      });

      const newGraphData = makeGraphDataWithGroup(['["asset_a"]'], 'mygroup');
      rerender({graphData: newGraphData});

      expect(result.current.overrides['global@global:mygroup']).toEqual({x: 100, y: 200});
    });

    it('prunes group overrides when the group no longer exists in the graph', () => {
      const graphData = makeGraphDataWithGroup(['["asset_a"]'], 'mygroup');
      const {result, rerender} = renderHook(
        ({graphData}: {graphData: GraphData}) => usePositionOverrides(STORAGE_KEY, graphData),
        {initialProps: {graphData}},
      );

      act(() => {
        result.current.updateNodePosition('global@global:mygroup', {x: 100, y: 200});
      });

      // Remove all nodes so no groups are registered
      rerender({graphData: makeGraphData([])});

      expect(result.current.overrides['global@global:mygroup']).toBeUndefined();
    });
  });

  describe('position clamping', () => {
    it('clamps negative x to 0 in updateNodePosition', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: -50, y: 100});
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 0, y: 100});
    });

    it('clamps negative y to 0 in updateNodePosition', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 100, y: -200});
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 100, y: 0});
    });

    it('does not clamp non-negative positions', () => {
      const graphData = makeGraphData(['["asset_a"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 0, y: 0});
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 0, y: 0});
    });

    it('clamps negative coordinates in updateMultiplePositions', () => {
      const graphData = makeGraphData(['["asset_a"]', '["asset_b"]']);
      const {result} = renderHook(() => usePositionOverrides(STORAGE_KEY, graphData));

      act(() => {
        result.current.updateMultiplePositions({
          '["asset_a"]': {x: -10, y: 50},
          '["asset_b"]': {x: 80, y: -30},
        });
      });

      expect(result.current.overrides['["asset_a"]']).toEqual({x: 0, y: 50});
      expect(result.current.overrides['["asset_b"]']).toEqual({x: 80, y: 0});
    });
  });

  describe('hasOverrides', () => {
    it('is false when no overrides exist', () => {
      const {result} = renderHook(() =>
        usePositionOverrides(STORAGE_KEY, makeGraphData(['["asset_a"]'])),
      );
      expect(result.current.hasOverrides).toBe(false);
    });

    it('is true when at least one override exists', () => {
      const {result} = renderHook(() =>
        usePositionOverrides(STORAGE_KEY, makeGraphData(['["asset_a"]'])),
      );
      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 1, y: 1});
      });
      expect(result.current.hasOverrides).toBe(true);
    });

    it('becomes false after reset', () => {
      const {result} = renderHook(() =>
        usePositionOverrides(STORAGE_KEY, makeGraphData(['["asset_a"]'])),
      );
      act(() => {
        result.current.updateNodePosition('["asset_a"]', {x: 1, y: 1});
      });
      act(() => {
        result.current.resetAllOverrides();
      });
      expect(result.current.hasOverrides).toBe(false);
    });
  });
});
