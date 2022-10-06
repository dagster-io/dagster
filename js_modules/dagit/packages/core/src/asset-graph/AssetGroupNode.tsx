import {Box, Colors, FontFamily, Icon, Mono} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {MINIMAL_SCALE, EXPERIMENTAL_SCALE} from './AssetGraphExplorer';
import {GroupLayout} from './layout';

export const AssetGroupNode: React.FC<{group: GroupLayout; scale: number}> = ({group, scale}) => {
  const {
    repositoryLocationName,
    repositoryDisambiguationRequired,
    repositoryName,
    groupName,
  } = group;

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      {scale > EXPERIMENTAL_SCALE && (
        <Box
          flex={{alignItems: 'flex-end'}}
          style={{
            height: 70,
          }}
        >
          <Mono
            style={{
              fontWeight: 600,
              userSelect: 'none',
              fontSize: scale > MINIMAL_SCALE ? '16px' : '32px',
              display: 'flex',
              gap: 6,
            }}
          >
            <Icon name="asset_group" size={scale > MINIMAL_SCALE ? 20 : 48} />
            <Box flex={{direction: 'column'}}>
              <Link
                style={{color: Colors.Gray900}}
                onClick={(e) => e.stopPropagation()}
                to={workspacePath(
                  repositoryName,
                  repositoryLocationName,
                  `/asset-groups/${groupName}`,
                )}
              >
                {groupName}
              </Link>
              {repositoryDisambiguationRequired && (
                <GroupRepoName style={{marginBottom: '0.5em'}}>
                  {withMiddleTruncation(buildRepoPath(repositoryName, repositoryLocationName), {
                    maxLength: 45,
                  })}
                </GroupRepoName>
              )}
            </Box>
          </Mono>
        </Box>
      )}

      <GroupOutline
        style={{
          inset: 0,
          top: 75,
          position: 'absolute',
          border: `${Math.max(2, 2 / scale)}px dashed ${Colors.Gray300}`,
          background:
            scale < EXPERIMENTAL_SCALE
              ? `rgba(243, 243, 243, 1)`
              : `rgba(223, 223, 223, ${0.4 - Math.max(0, scale - MINIMAL_SCALE) * 0.3})`,
        }}
      />

      {scale < EXPERIMENTAL_SCALE ? (
        <Box
          flex={{justifyContent: 'center', alignItems: 'center'}}
          style={{inset: 0, position: 'absolute', fontSize: `${14 / scale}px`, userSelect: 'none'}}
        >
          <Box
            flex={{direction: 'column'}}
            style={{fontWeight: 600, fontFamily: FontFamily.monospace}}
          >
            {groupName}
            {repositoryDisambiguationRequired && (
              <GroupRepoName>
                {withMiddleTruncation(buildRepoPath(repositoryName, repositoryLocationName), {
                  maxLength: 45,
                })}
              </GroupRepoName>
            )}
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
`;
