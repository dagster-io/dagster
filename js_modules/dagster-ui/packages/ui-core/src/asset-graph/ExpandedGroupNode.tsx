import {Box, ButtonLink, Colors, FontFamily} from '@dagster-io/ui-components';
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
        <GroupNodeHeaderBox $minimal={minimal}>
          <GroupNodeNameAndRepo group={group} minimal={minimal} />
        </GroupNodeHeaderBox>
      )}
      <Box padding={{horizontal: 8, vertical: 4}}>
        <ButtonLink onClick={onCollapse}>Collapse</ButtonLink>
      </Box>
      <GroupOutline
        $minimal={minimal}
        style={{
          inset: 0,
          top: 60,
          position: 'absolute',
          background:
            scale < GROUPS_ONLY_SCALE ? `rgba(234, 234, 234, 1)` : `rgba(217, 217, 217, 0.25)`,
        }}
      />

      {scale < GROUPS_ONLY_SCALE ? (
        <Box
          flex={{justifyContent: 'center', alignItems: 'center'}}
          style={{inset: 0, position: 'absolute', fontSize: `${12 / scale}px`, userSelect: 'none'}}
        >
          <Box
            flex={{direction: 'column', alignItems: 'center'}}
            style={{fontWeight: 600, fontFamily: FontFamily.monospace}}
          >
            {groupName}
            <GroupRepoName>
              {withMiddleTruncation(buildRepoPathForHuman(repositoryName, repositoryLocationName), {
                maxLength: 48,
              })}
            </GroupRepoName>
          </Box>
        </Box>
      ) : undefined}
    </div>
  );
};

const GroupOutline = styled.div<{$minimal: boolean}>`
  width: 100%;
  border-radius: 10px;
  border-top-left-radius: 0;
  pointer-events: none;
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.Gray200};
`;

const GroupRepoName = styled.div`
  font-size: 0.8em;
  line-height: 0.6em;
  white-space: nowrap;
  color: ${Colors.Gray400};
`;

const GroupNodeHeaderBox = styled.div<{$minimal: boolean}>`
  border: ${(p) => (p.$minimal ? '4px' : '2px')} solid ${Colors.Gray200};
  background: ${Colors.White};
  max-width: 300px;
  border-radius: 8px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: 0;
  position: relative;
`;
