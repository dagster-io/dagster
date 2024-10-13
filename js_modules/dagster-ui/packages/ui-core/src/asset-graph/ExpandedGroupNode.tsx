import {Box, Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {GroupNodeNameAndRepo, useGroupNodeContextMenu} from './CollapsedGroupNode';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {GraphNode} from './Utils';
import {GroupLayout} from './layout';
import {SVGRelativeContainerForSafari} from '../graph/SVGComponents';

export const ExpandedGroupNode = ({
  group,
  minimal,
  onCollapse,
  toggleSelectAllNodes,
  preferredJobName,
  onFilterToGroup,
  setHighlighted,
}: {
  group: GroupLayout & {assets: GraphNode[]};
  minimal: boolean;
  onCollapse?: () => void;
  toggleSelectAllNodes?: (e: React.MouseEvent) => void;
  preferredJobName?: string;
  onFilterToGroup?: () => void;
  setHighlighted: (ids: string[] | null) => void;
}) => {
  const {menu, dialog} = useGroupNodeContextMenu({
    onFilterToGroup,
    assets: group.assets,
    preferredJobName,
  });
  return (
    <SVGRelativeContainerForSafari>
      <ContextMenuWrapper menu={menu} stopPropagation>
        <GroupNodeHeaderBox
          $minimal={minimal}
          onMouseEnter={() => setHighlighted(group.assets.map((a) => a.id))}
          onMouseLeave={() => setHighlighted(null)}
          onClick={(e) => {
            if (e.metaKey && toggleSelectAllNodes) {
              toggleSelectAllNodes(e);
            } else {
              onCollapse?.();
            }
            e.stopPropagation();
          }}
        >
          <GroupNodeNameAndRepo group={group} minimal={minimal} />
          {onCollapse && (
            <Box padding={{vertical: 4}}>
              <Icon name="unfold_less" />
            </Box>
          )}
        </GroupNodeHeaderBox>
      </ContextMenuWrapper>
      {dialog}
    </SVGRelativeContainerForSafari>
  );
};

export const GroupOutline = ({minimal}: {minimal: boolean}) => (
  <SVGRelativeContainerForSafari>
    <GroupOutlineBox $minimal={minimal} />
  </SVGRelativeContainerForSafari>
);

const GroupOutlineBox = styled.div<{$minimal: boolean}>`
  inset: 0;
  top: 60px;
  position: absolute;
  background: ${Colors.lineageGroupBackground()};
  width: 100%;
  border-radius: 10px;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  pointer-events: none;

  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.lineageGroupNodeBorder()};
  border-top: 0;
`;

const GroupNodeHeaderBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.lineageGroupNodeBorder()};
  background: ${Colors.lineageGroupNodeBackground()};
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 12px 0 16px;
  border-radius: 8px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  position: relative;
  transition:
    background 100ms linear,
    border-color 100ms linear;

  &:hover {
    background: ${Colors.lineageGroupNodeBackgroundHover()};
    border-color: ${Colors.lineageGroupNodeBorderHover()};
  }
`;
