import {Box, ButtonLink, Colors, FontFamily, Icon, Button} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {withMiddleTruncation} from '../app/Util';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

import {GROUPS_ONLY_SCALE} from './AssetGraphExplorer';
import {GroupNodeNameAndRepo} from './CollapsedGroupNode';
import {GroupLayout} from './layout';

export const ExpandedGroupNode: React.FC<{
  group: GroupLayout;
  scale: number;
  minimal: boolean;
  onCollapse: () => void;
}> = ({group, minimal, scale, onCollapse}) => {
  const {repositoryLocationName, repositoryName, groupName} = group;

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      {scale > GROUPS_ONLY_SCALE && (
        <GroupNodeHeaderBox 
          $minimal={minimal}
          onClick={onCollapse} 
        >
          <GroupNodeNameAndRepo group={group} minimal={minimal} />
          <Icon size={24} color={Colors.Gray500} name="unfold_less" />

        </GroupNodeHeaderBox>
      )}
      <GroupOutline
        $minimal={minimal}
        style={{
          inset: 0,
          top: 0,
          position: 'absolute',
          zIndex: -1,
          background: `rgba(255, 255, 255, .4)`,
        }}
      />

      {scale < GROUPS_ONLY_SCALE ? (
        <Box
          flex={{justifyContent: 'center', alignItems: 'center'}}
          style={{inset: 0, position: 'absolute', fontSize: `${12 / scale}px`, userSelect: 'none'}}
        >
        </Box>
      ) : undefined}
    </div>
  );
};

const GroupOutline = styled.div<{$minimal: boolean}>`
  width: 100%;
  border-radius: 12px;
  pointer-events: none;
  border: ${(p) => (p.$minimal ? '2px' : '2px')} solid ${Colors.KeylineGray};
`;

const GroupRepoName = styled.div`
  font-size: 0.8em;
  line-height: 0.6em;
  white-space: nowrap;
  color: ${Colors.Gray400};
`;

const GroupNodeHeaderBox = styled.div<{$minimal: boolean}>`
  border: 2px solid ${Colors.KeylineGray};
  background: ${Colors.Gray50};
  color: ${Colors.Gray900};
  max-width: 100%;
  border-radius: 12px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: 0;
  position: relative;
  transition: background 200ms ease-in-out;
  cursor: pointer;
  display: flex; 
  flex-direction: row; 
  justify-content: space-between;
  align-items: center; 
  padding: 6px 12px;
  :hover {
    background: ${Colors.Gray100};
  }
`;
