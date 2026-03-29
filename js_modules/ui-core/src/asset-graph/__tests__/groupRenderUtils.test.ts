import {getGroupBoundsForRender} from '../groupRenderUtils';
import {AssetLayout, GroupLayout} from '../layout';

const makeGroup = (overrides: Partial<GroupLayout> = {}): GroupLayout => ({
  id: 'group@repo:loc',
  groupName: 'group',
  repositoryName: 'repo',
  repositoryLocationName: 'loc',
  bounds: {x: 100, y: 200, width: 400, height: 160},
  expanded: true,
  ...overrides,
});

const makeNodes = (overrides: Record<string, AssetLayout> = {}): Record<string, AssetLayout> => ({
  '["asset_a"]': {id: '["asset_a"]', bounds: {x: 120, y: 240, width: 120, height: 80}},
  '["asset_b"]': {id: '["asset_b"]', bounds: {x: 280, y: 240, width: 120, height: 80}},
  ...overrides,
});

describe('getGroupBoundsForRender', () => {
  it('translates expanded group bounds while the group is being dragged', () => {
    const group = makeGroup();
    const nodes = makeNodes();

    const result = getGroupBoundsForRender({
      group,
      draggingGroupId: group.id,
      childNodeIds: ['["asset_a"]', '["asset_b"]'],
      draggedNodePositions: {'["asset_a"]': {x: 180, y: 300}},
      nodes,
    });

    expect(result).toEqual({...group.bounds, x: 160, y: 260});
  });

  it('uses the dragged group position directly for collapsed groups', () => {
    const group = makeGroup({expanded: false});

    const result = getGroupBoundsForRender({
      group,
      draggingGroupId: group.id,
      childNodeIds: [],
      draggedNodePositions: {['group@repo:loc']: {x: 450, y: 480}},
      nodes: makeNodes(),
    });

    expect(result).toEqual({...group.bounds, x: 450, y: 480});
  });

  it('returns the original bounds when an expanded group has no dragged child positions', () => {
    const group = makeGroup();

    const result = getGroupBoundsForRender({
      group,
      draggingGroupId: group.id,
      childNodeIds: ['["asset_a"]', '["asset_b"]'],
      draggedNodePositions: {},
      nodes: makeNodes(),
    });

    expect(result).toEqual(group.bounds);
  });
});
