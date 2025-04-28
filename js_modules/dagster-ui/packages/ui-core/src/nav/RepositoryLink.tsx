import {
  Box,
  Colors,
  Icon,
  IconWrapper,
  MiddleTruncate,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  NO_RELOAD_PERMISSION_TEXT,
  ReloadRepositoryLocationButton,
} from './ReloadRepositoryLocationButton';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const RepositoryLink = ({
  repoAddress,
  showIcon = false,
  showRefresh = true,
}: {
  repoAddress: RepoAddress;
  showIcon?: boolean;
  showRefresh?: boolean;
}) => {
  const {location} = repoAddress;
  const repoString = repoAddressAsHumanString(repoAddress);

  return (
    <Box flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}} title={repoString}>
      {showIcon && <Icon name="folder" style={{marginRight: 8}} color={Colors.accentGray()} />}
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
                      color={hasReloadPermission ? Colors.accentGray() : Colors.accentGrayHover()}
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
    color: ${Colors.accentBlue()};
  }
`;
