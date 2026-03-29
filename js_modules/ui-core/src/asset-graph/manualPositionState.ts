import {IPoint} from '../graph/common';

export const getGroupManualPositionState = (
  overrides: Record<string, IPoint>,
  groupId: string,
) => ({
  isManuallyPositioned: !!overrides[groupId],
  resetIds: overrides[groupId] ? [groupId] : [],
});
