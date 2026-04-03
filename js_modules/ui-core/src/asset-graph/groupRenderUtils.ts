import {AssetLayout, GroupLayout} from './layout';
import {IBounds, IPoint} from '../graph/common';

export const getGroupBoundsForRender = ({
  group,
  draggingGroupId,
  childNodeIds,
  draggedNodePositions,
  nodes,
}: {
  group: GroupLayout;
  draggingGroupId: string | null;
  childNodeIds: string[];
  draggedNodePositions: Record<string, IPoint>;
  nodes: Record<string, AssetLayout>;
}): IBounds => {
  if (!group.expanded) {
    const dragPos = draggedNodePositions[group.id];
    return dragPos ? {...group.bounds, x: dragPos.x, y: dragPos.y} : group.bounds;
  }

  if (draggingGroupId !== group.id) {
    return group.bounds;
  }

  const firstDraggedChildId = childNodeIds.find((id) => draggedNodePositions[id]);
  if (!firstDraggedChildId) {
    return group.bounds;
  }

  const dragPos = draggedNodePositions[firstDraggedChildId];
  if (!dragPos) {
    return group.bounds;
  }
  const originalBounds = nodes[firstDraggedChildId]?.bounds;
  if (!originalBounds) {
    return group.bounds;
  }

  return {
    ...group.bounds,
    x: group.bounds.x + (dragPos.x - originalBounds.x),
    y: group.bounds.y + (dragPos.y - originalBounds.y),
  };
};
