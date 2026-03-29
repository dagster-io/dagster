import {applyPositionOverrides} from '../applyLayoutOverrides';
import {AssetGraphLayout} from '../layout';

/** Build a minimal AssetGraphLayout for testing */
function makeLayout(overrides: Partial<AssetGraphLayout> = {}): AssetGraphLayout {
  return {
    width: 1000,
    height: 800,
    edges: [],
    nodes: {},
    groups: {},
    linkNodeIds: [],
    ...overrides,
  };
}

describe('applyPositionOverrides', () => {
  describe('when overrides is empty', () => {
    it('returns the original layout object unchanged', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
        },
      });
      const result = applyPositionOverrides(layout, {}, 'vertical');
      expect(result).toBe(layout); // exact same reference
    });
  });

  describe('node position overrides', () => {
    it('applies x/y override to the matched node', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
          '["asset_b"]': {id: '["asset_b"]', bounds: {x: 500, y: 100, width: 320, height: 100}},
        },
      });

      const result = applyPositionOverrides(layout, {'["asset_a"]': {x: 50, y: 200}}, 'vertical');

      expect(result.nodes['["asset_a"]']?.bounds.x).toBe(50);
      expect(result.nodes['["asset_a"]']?.bounds.y).toBe(200);
      // width and height must be preserved
      expect(result.nodes['["asset_a"]']?.bounds.width).toBe(320);
      expect(result.nodes['["asset_a"]']?.bounds.height).toBe(100);
    });

    it('does not mutate nodes that have no override', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
          '["asset_b"]': {id: '["asset_b"]', bounds: {x: 500, y: 100, width: 320, height: 100}},
        },
      });

      const result = applyPositionOverrides(layout, {'["asset_a"]': {x: 50, y: 200}}, 'vertical');

      expect(result.nodes['["asset_b"]']).toBe(layout.nodes['["asset_b"]']); // same reference
    });

    it('does not mutate the original layout', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
        },
      });

      applyPositionOverrides(layout, {'["asset_a"]': {x: 50, y: 200}}, 'vertical');

      // Original must be untouched
      expect(layout.nodes['["asset_a"]']?.bounds.x).toBe(100);
      expect(layout.nodes['["asset_a"]']?.bounds.y).toBe(100);
    });

    it('handles multiple simultaneous overrides', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
          '["asset_b"]': {id: '["asset_b"]', bounds: {x: 500, y: 100, width: 320, height: 100}},
          '["asset_c"]': {id: '["asset_c"]', bounds: {x: 900, y: 100, width: 320, height: 100}},
        },
      });

      const result = applyPositionOverrides(
        layout,
        {
          '["asset_a"]': {x: 0, y: 0},
          '["asset_b"]': {x: 200, y: 400},
        },
        'vertical',
      );

      expect(result.nodes['["asset_a"]']?.bounds).toMatchObject({x: 0, y: 0});
      expect(result.nodes['["asset_b"]']?.bounds).toMatchObject({x: 200, y: 400});
      expect(result.nodes['["asset_c"]']?.bounds).toMatchObject({x: 900, y: 100}); // unchanged
    });
  });

  describe('edge recomputation', () => {
    it('recomputes edge endpoints when a connected node moves (vertical)', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 0, width: 320, height: 100}},
          '["asset_b"]': {id: '["asset_b"]', bounds: {x: 100, y: 200, width: 320, height: 100}},
        },
        edges: [
          {
            fromId: '["asset_a"]',
            from: {x: 124, y: 70}, // x+24, y+height-30
            toId: '["asset_b"]',
            to: {x: 124, y: 220}, // x+24, y+20
          },
        ],
      });

      const result = applyPositionOverrides(layout, {'["asset_a"]': {x: 0, y: 0}}, 'vertical');

      // from.x should reflect new x=0 + xInset(24) = 24
      expect(result.edges[0]?.from.x).toBe(24);
      // to should remain relative to asset_b (unchanged)
      expect(result.edges[0]?.to.x).toBe(124);
    });

    it('recomputes edge endpoints when a connected node moves (horizontal)', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 0, y: 0, width: 320, height: 100}},
          '["asset_b"]': {id: '["asset_b"]', bounds: {x: 500, y: 0, width: 320, height: 100}},
        },
        edges: [
          {
            fromId: '["asset_a"]',
            from: {x: 320, y: 50},
            toId: '["asset_b"]',
            to: {x: 495, y: 50},
          },
        ],
      });

      const result = applyPositionOverrides(layout, {'["asset_a"]': {x: 100, y: 0}}, 'horizontal');

      // from.x = new x + width = 100 + 320 = 420
      expect(result.edges[0]?.from.x).toBe(420);
      expect(result.edges[0]?.from.y).toBe(50);
    });

    it('preserves edges whose nodes are not in the layout', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 0, y: 0, width: 320, height: 100}},
        },
        edges: [
          {
            fromId: '["asset_a"]',
            from: {x: 0, y: 0},
            toId: '["unknown"]', // not in nodes
            to: {x: 999, y: 999},
          },
        ],
      });

      const result = applyPositionOverrides(layout, {'["asset_a"]': {x: 50, y: 50}}, 'vertical');

      // Edge with missing toId node is returned as-is
      expect(result.edges[0]?.to).toEqual({x: 999, y: 999});
    });
  });

  describe('stale override IDs', () => {
    it('ignores overrides for nodes not present in the layout', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
        },
      });

      // '["stale_node"]' is no longer in the layout
      const result = applyPositionOverrides(
        layout,
        {
          '["asset_a"]': {x: 50, y: 50},
          '["stale_node"]': {x: 999, y: 999},
        },
        'vertical',
      );

      expect(result.nodes['["stale_node"]']).toBeUndefined();
      expect(result.nodes['["asset_a"]']?.bounds.x).toBe(50);
    });
  });

  describe('canvas extent recomputation', () => {
    it('expands canvas when a node is moved beyond original extents', () => {
      const layout = makeLayout({
        width: 500,
        height: 300,
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 100, width: 320, height: 100}},
        },
      });

      const result = applyPositionOverrides(
        layout,
        {'["asset_a"]': {x: 2000, y: 2000}},
        'vertical',
      );

      // Canvas must accommodate the moved node: 2000 + 320 + 100 margin = 2420
      expect(result.width).toBeGreaterThan(2000);
      expect(result.height).toBeGreaterThan(2000);
    });
  });

  describe('collapsed group overrides', () => {
    it('applies x/y override to a collapsed group', () => {
      const layout = makeLayout({
        groups: {
          'group@repo:loc': {
            id: 'group@repo:loc',
            groupName: 'group',
            repositoryName: 'repo',
            repositoryLocationName: 'loc',
            bounds: {x: 100, y: 100, width: 400, height: 200},
            expanded: false,
          },
        },
      });

      const result = applyPositionOverrides(
        layout,
        {'group@repo:loc': {x: 500, y: 600}},
        'vertical',
      );

      expect(result.groups['group@repo:loc']?.bounds.x).toBe(500);
      expect(result.groups['group@repo:loc']?.bounds.y).toBe(600);
      // width and height preserved
      expect(result.groups['group@repo:loc']?.bounds.width).toBe(400);
      expect(result.groups['group@repo:loc']?.bounds.height).toBe(200);
    });

    it('uses overridden collapsed group bounds for edge recomputation', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 0, width: 320, height: 100}},
        },
        groups: {
          'group@repo:loc': {
            id: 'group@repo:loc',
            groupName: 'group',
            repositoryName: 'repo',
            repositoryLocationName: 'loc',
            bounds: {x: 100, y: 200, width: 400, height: 200},
            expanded: false,
          },
        },
        edges: [
          {
            fromId: '["asset_a"]',
            from: {x: 124, y: 70},
            toId: 'group@repo:loc',
            to: {x: 124, y: 220},
          },
        ],
      });

      const result = applyPositionOverrides(
        layout,
        {'group@repo:loc': {x: 500, y: 500}},
        'vertical',
      );

      // to.x should reflect new group position: 500 + xInset(24) = 524
      expect(result.edges[0]?.to.x).toBe(524);
      expect(result.edges[0]?.to.y).toBe(520); // 500 + 20
    });
  });

  describe('link node xInset', () => {
    it('uses xInset=16 for link nodes in vertical direction', () => {
      const layout = makeLayout({
        nodes: {
          '["asset_a"]': {id: '["asset_a"]', bounds: {x: 100, y: 0, width: 320, height: 100}},
          '["link_node"]': {id: '["link_node"]', bounds: {x: 100, y: 200, width: 320, height: 100}},
        },
        edges: [
          {
            fromId: '["asset_a"]',
            from: {x: 124, y: 70},
            toId: '["link_node"]',
            to: {x: 116, y: 220}, // xInset=16 for link node
          },
        ],
        linkNodeIds: ['["link_node"]'],
      });

      const result = applyPositionOverrides(layout, {'["asset_a"]': {x: 0, y: 0}}, 'vertical');

      // from.x = 0 + 24 (regular node default xInset)
      expect(result.edges[0]?.from.x).toBe(24);
      // to.x = 100 + 16 (link node xInset=16)
      expect(result.edges[0]?.to.x).toBe(116);
    });
  });
});
