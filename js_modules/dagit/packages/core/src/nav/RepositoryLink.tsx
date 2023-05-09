import {Box, Colors, Icon, IconWrapper, MiddleTruncate, Spinner, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from './ReloadRepositoryLocationButton';

export const RepositoryLink: React.FC<{
  repoAddress: RepoAddress;
  showIcon?: boolean;
  showRefresh?: boolean;
}> = ({repoAddress, showIcon = false, showRefresh = true}) => {
  const {location} = repoAddress;
  const repoString = repoAddressAsHumanString(repoAddress);

  return (
    <Box flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}} title={repoString}>
      {showIcon && <Icon name="folder" style={{marginRight: 8}} color={Colors.Gray400} />}
      <RepositoryName to={workspacePathFromAddress(repoAddress)} style={{flex: 1}}>
        <MiddleTruncate text={repoString} />
      </RepositoryName>
      {showRefresh ? (
        <ReloadRepositoryLocationButton
          location={location}
          ChildComponent={({codeLocation, tryReload, reloading, hasReloadPermission}) => {
            const tooltipContent = () => {
              if (!hasReloadPermission) {
                return NO_RELOAD_PERMISSION_TEXT;
              }

              return reloading ? (
                'Reloading…'
              ) : (
                <>
                  Reload location <strong>{codeLocation}</strong>
                </>
              );
            };

            return (
              <ReloadTooltip content={tooltipContent()}>
                {reloading ? (
                  <Spinner purpose="body-text" />
                ) : (
                  <StyledButton disabled={!hasReloadPermission} onClick={tryReload}>
                    <Icon
                      name="refresh"
                      color={hasReloadPermission ? Colors.Gray400 : Colors.Gray300}
                    />
                  </StyledButton>
                )}
              </ReloadTooltip>
            );
          }}
        />
      ) : null}
    </Box>
  );
};

export const RepositoryName = styled(Link)`
  max-width: 280px;
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

  :disabled {
    cursor: default;
  }

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
