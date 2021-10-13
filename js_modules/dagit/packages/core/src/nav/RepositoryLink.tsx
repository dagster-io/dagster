import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP, IconWrapper} from '../ui/Icon';
import {Spinner} from '../ui/Spinner';
import {Tooltip} from '../ui/Tooltip';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';

export const RepositoryLink: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {location} = repoAddress;
  const {canReloadRepositoryLocation} = usePermissions();

  return (
    <Box flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}}>
      <RepositoryName
        to={workspacePathFromAddress(repoAddress)}
        title={repoAddressAsString(repoAddress)}
      >
        {repoAddressAsString(repoAddress)}
      </RepositoryName>
      {canReloadRepositoryLocation ? (
        <ReloadRepositoryLocationButton location={location}>
          {({tryReload, reloading}) => (
            <ReloadTooltip
              content={
                reloading ? (
                  'Reloading…'
                ) : (
                  <>
                    Reload location <strong>{location}</strong>
                  </>
                )
              }
            >
              {reloading ? (
                <Spinner purpose="body-text" />
              ) : (
                <StyledButton onClick={tryReload}>
                  <IconWIP name="refresh" color={ColorsWIP.Gray400} />
                </StyledButton>
              )}
            </ReloadTooltip>
          )}
        </ReloadRepositoryLocationButton>
      ) : null}
    </Box>
  );
};

const RepositoryName = styled(Link)`
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ReloadTooltip = styled(Tooltip)`
  margin-left: 4px;

  && {
    display: block;
  }
`;

const StyledButton = styled.button`
  background-color: transparent;
  border: 0;
  cursor: pointer;
  display: block;
  padding: 0;
  margin: 0;

  :focus:not(:focus-visible) {
    outline: none;
  }

  & ${IconWrapper} {
    display: block;
    transition: color 100ms linear;
  }

  :hover ${IconWrapper} {
    color: ${ColorsWIP.Blue500};
  }
`;
