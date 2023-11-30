import {
  Box,
  FontFamily,
  Icon,
  Mono,
  colorAccentBlue,
  colorLineageGroupNodeBorder,
  colorTextLight,
} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {withMiddleTruncation} from '../app/Util';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {MINIMAL_SCALE, GROUPS_ONLY_SCALE} from './AssetGraphExplorer';
import {GroupLayout} from './layout';

interface Props {
  group: GroupLayout;
  scale: number;
}

export const AssetGroupNode = ({group, scale}: Props) => {
  const {repositoryLocationName, repositoryName, groupName} = group;

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      {scale > GROUPS_ONLY_SCALE && (
        <Box flex={{alignItems: 'flex-end'}} style={{height: 70}}>
          <Mono
            style={{
              fontWeight: 600,
              userSelect: 'none',
              fontSize: scale > MINIMAL_SCALE ? '16px' : '32px',
              display: 'flex',
              gap: 6,
            }}
          >
            <Icon
              name="asset_group"
              color={colorTextLight()}
              size={scale > MINIMAL_SCALE ? 20 : 48}
            />
            <Box flex={{direction: 'column'}}>
              <Link
                style={{color: colorTextLight()}}
                onClick={(e) => e.stopPropagation()}
                to={workspacePath(
                  repositoryName,
                  repositoryLocationName,
                  `/asset-groups/${groupName}`,
                )}
              >
                {groupName}
              </Link>
              <GroupRepoName style={{marginBottom: '0.5em'}}>
                {withMiddleTruncation(
                  buildRepoPathForHuman(repositoryName, repositoryLocationName),
                  {
                    maxLength: 45,
                  },
                )}
              </GroupRepoName>
            </Box>
          </Mono>
        </Box>
      )}

      <GroupOutline
        style={{
          inset: 0,
          top: 75,
          position: 'absolute',
          background:
            scale < GROUPS_ONLY_SCALE
              ? colorLineageGroupNodeBorder()
              : colorLineageGroupNodeBorder(),
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
                maxLength: 45,
              })}
            </GroupRepoName>
          </Box>
        </Box>
      ) : undefined}
    </div>
  );
};

const GroupOutline = styled.div`
  width: 100%;
  border-radius: 10px;
  pointer-events: none;
`;

const GroupRepoName = styled.div`
  font-size: 0.8em;
  line-height: 0.6em;
  white-space: nowrap;
  color: ${colorTextLight()};
`;
