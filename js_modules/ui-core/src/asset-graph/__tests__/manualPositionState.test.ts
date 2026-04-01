import {getGroupManualPositionState} from '../manualPositionState';

describe('getGroupManualPositionState', () => {
  const groupId = 'global@global:analytics';
  const childNodeIds = ['["analytics", "orders_daily"]', '["analytics", "customers_daily"]'];

  it('does not mark the group as manually positioned when only child overrides exist', () => {
    expect(
      getGroupManualPositionState(
        {
          '["analytics", "orders_daily"]': {x: 100, y: 200},
        },
        groupId,
        childNodeIds,
        false,
      ),
    ).toEqual({
      isManuallyPositioned: false,
      resetIds: [],
    });
  });

  it('marks a collapsed group as manually positioned and only resets the group override', () => {
    expect(
      getGroupManualPositionState(
        {
          [groupId]: {x: 10, y: 20},
          '["analytics", "orders_daily"]': {x: 100, y: 200},
        },
        groupId,
        childNodeIds,
        false,
      ),
    ).toEqual({
      isManuallyPositioned: true,
      resetIds: [groupId],
    });
  });

  it('resets expanded group child overrides together with the group override', () => {
    expect(
      getGroupManualPositionState(
        {
          [groupId]: {x: 10, y: 20},
          '["analytics", "orders_daily"]': {x: 100, y: 200},
          '["analytics", "customers_daily"]': {x: 120, y: 220},
          '["other", "asset"]': {x: 50, y: 60},
        },
        groupId,
        childNodeIds,
        true,
      ),
    ).toEqual({
      isManuallyPositioned: true,
      resetIds: [groupId, ...childNodeIds],
    });
  });
});
