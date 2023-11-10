import {Box, Colors, Icon} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {GroupNodeNameAndRepo} from './CollapsedGroupNode';
import {GroupLayout} from './layout';

export const ExpandedGroupNode = ({
  group,
  minimal,
  onCollapse,
}: {
  group: GroupLayout;
  minimal: boolean;
  onCollapse?: () => void;
}) => {
  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
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
      <GroupOutline $minimal={minimal} />
    </div>
  );
};

const GroupOutline = styled.div<{$minimal: boolean}>`
  inset: 0;
  top: 60px;
  position: absolute;
  background: ${Colors.White};
  width: 100%;
  border-radius: 10px;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  pointer-events: none;

  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.Gray200};
`;

const GroupNodeHeaderBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.Gray200};
  background: ${Colors.Gray50};
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

  &:hover {
    background: ${Colors.Gray100};
  }
`;
