import {Box, Colors, Icon, Mono} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {MINIMAL_SCALE} from './AssetGraphExplorer';
import {GroupLayout} from './layout';

export const AssetGroupNode: React.FC<{group: GroupLayout; scale: number}> = ({group, scale}) => {
  const {
    repositoryLocationName,
    repositoryDisambiguationRequired,
    repositoryName,
    groupName,
  } = group;

  return (
    <>
      <Mono
        style={{
          opacity: scale > MINIMAL_SCALE ? (scale - MINIMAL_SCALE) / 0.2 : 0,
          fontWeight: 600,
          display: 'flex',
          gap: 6,
        }}
      >
        <Icon name="asset_group" size={20} />
        <Box flex={{direction: 'column'}}>
          <Link
            style={{color: Colors.Gray900}}
            onClick={(e) => e.stopPropagation()}
            to={workspacePath(repositoryName, repositoryLocationName, `/asset-groups/${groupName}`)}
          >
            {groupName}
          </Link>
          {repositoryDisambiguationRequired && (
            <GroupRepoName>
              {withMiddleTruncation(buildRepoPath(repositoryName, repositoryLocationName), {
                maxLength: 45,
              })}
            </GroupRepoName>
          )}
        </Box>
      </Mono>

      <GroupOutline
        style={{
          marginTop: 6,
          height: group.bounds.height - (repositoryDisambiguationRequired ? 24 + 18 : 24) - 3,
          border: `${Math.max(2, 2 / scale)}px dashed ${Colors.Gray300}`,
          background: `rgba(223, 223, 223, ${0.4 - Math.max(0, scale - MINIMAL_SCALE) * 0.3})`,
        }}
      />
    </>
  );
};

const GroupOutline = styled.div`
  width: 100%;
  border-radius: 10px;
  pointer-events: none;
`;

const GroupRepoName = styled.div`
  font-size: 0.8rem;
  line-height: 0.7rem;
  white-space: nowrap;
  margin-bottom: 4px;
`;
