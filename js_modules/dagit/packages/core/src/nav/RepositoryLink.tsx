import {Box, Colors, Icon, IconWrapper, MiddleTruncate, Spinner, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';

export const RepositoryLink: React.FC<{
  repoAddress: RepoAddress;
  showIcon?: boolean;
  showRefresh?: boolean;
}> = ({repoAddress, showIcon = false, showRefresh = true}) => {
  const {location} = repoAddress;
  const {canReloadRepositoryLocation} = usePermissions();
  const repoString = repoAddressAsString(repoAddress);

  return (
    <Box flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}} title={repoString}>
      {showIcon && <Icon name="folder" style={{marginRight: 8}} color={Colors.Gray400} />}
      <RepositoryName to={workspacePathFromAddress(repoAddress)} style={{flex: 1}}>
        <MiddleTruncate text={repoString} />
      </RepositoryName>
      {canReloadRepositoryLocation.enabled && showRefresh ? (
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
                  <Icon name="refresh" color={Colors.Gray400} />
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
  min-width: 150px;
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
    color: ${Colors.Blue500};
  }
`;
