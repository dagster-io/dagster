import {IPoint} from '../graph/common';

export const getGroupManualPositionState = (
  overrides: Record<string, IPoint>,
  groupId: string,
  childNodeIds: string[] = [],
  isExpanded: boolean = false,
) => {
  const ownedIds = isExpanded ? [groupId, ...childNodeIds] : [groupId];
  const resetIds = ownedIds.filter((id) => !!overrides[id]);

  return {
    isManuallyPositioned: resetIds.length > 0,
    resetIds,
  };
};
