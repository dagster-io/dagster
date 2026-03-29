import {getGroupManualPositionState} from '../manualPositionState';

describe('getGroupManualPositionState', () => {
  const groupId = 'global@global:analytics';

  it('does not mark the group as manually positioned when only child overrides exist', () => {
    expect(
      getGroupManualPositionState(
        {
          '["analytics", "orders_daily"]': {x: 100, y: 200},
        },
        groupId,
      ),
    ).toEqual({
      isManuallyPositioned: false,
      resetIds: [],
    });
  });

  it('marks the group as manually positioned and only resets the group override', () => {
    expect(
      getGroupManualPositionState(
        {
          [groupId]: {x: 10, y: 20},
          '["analytics", "orders_daily"]': {x: 100, y: 200},
        },
        groupId,
      ),
    ).toEqual({
      isManuallyPositioned: true,
      resetIds: [groupId],
    });
  });
});
