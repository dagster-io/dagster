import {
  Box,
  Icon,
  colorLineageGroupBackground,
  colorLineageGroupNodeBorder,
  colorLineageGroupNodeBackground,
  colorLineageGroupNodeBackgroundHover,
  colorLineageGroupNodeBorderHover,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {GroupNodeNameAndRepo, useGroupNodeContextMenu} from './CollapsedGroupNode';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {GraphNode} from './Utils';
import {GroupLayout} from './layout';

export const ExpandedGroupNode = ({
  group,
  minimal,
  onCollapse,
  preferredJobName,
  onFilterToGroup,
}: {
  group: GroupLayout & {assets: GraphNode[]};
  minimal: boolean;
  onCollapse?: () => void;
  preferredJobName?: string;
  onFilterToGroup?: () => void;
}) => {
  const {menu, dialog} = useGroupNodeContextMenu({
    onFilterToGroup,
    assets: group.assets,
    preferredJobName,
  });
  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <ContextMenuWrapper menu={menu} stopPropagation>
        <GroupNodeHeaderBox
          $minimal={minimal}
          onClick={(e) => {
            onCollapse?.();
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
      <GroupOutline $minimal={minimal} />
      {dialog}
    </div>
  );
};

const GroupOutline = styled.div<{$minimal: boolean}>`
  inset: 0;
  top: 60px;
  position: absolute;
  background: ${colorLineageGroupBackground()};
  width: 100%;
  border-radius: 10px;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  pointer-events: none;

  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${colorLineageGroupNodeBorder()};
`;

const GroupNodeHeaderBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${colorLineageGroupNodeBorder()};
  background: ${colorLineageGroupNodeBackground()};
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 12px 0 16px;
  border-radius: 8px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: 0;
  position: relative;
  transition:
    background 100ms linear,
    border-color 100ms linear;

  &:hover {
    background: ${colorLineageGroupNodeBackgroundHover()};
    border-color: ${colorLineageGroupNodeBorderHover()};
  }
`;
