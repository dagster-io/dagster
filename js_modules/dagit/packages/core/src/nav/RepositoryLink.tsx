import {Icon, Colors} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {useRepositoryLocationReload} from './ReloadRepositoryLocationButton';

export const RepositoryLink: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {location} = repoAddress;
  const {reloading, onClick} = useRepositoryLocationReload(repoAddress.location);
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
        <ShortcutHandler
          onShortcut={onClick}
          shortcutLabel={`⌥R`}
          shortcutFilter={(e) => e.code === 'KeyR' && e.altKey}
        >
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
              <StyledButton onClick={onClick}>
                <Icon icon="refresh" iconSize={11} color={Colors.GRAY2} />
              </StyledButton>
            )}
          </ReloadTooltip>
        </ShortcutHandler>
      ) : null}
    </Box>
  );
};

const RepositoryName = styled(Link)`
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ReloadTooltip = styled(Tooltip)`
  margin-left: 8px;
  position: relative;
  top: 1px;

  .bp3-popover-target {
    display: block;
  }
`;

const StyledButton = styled.button`
  background-color: transparent;
  border: 0;
  cursor: pointer;
  padding: 0;
  margin: 0;

  :focus:not(:focus-visible) {
    outline: none;
  }

  .bp3-icon {
    display: block;
  }

  .bp3-icon svg {
    transition: fill 0.1s ease-in-out;
  }

  :hover .bp3-icon svg {
    fill: ${Colors.BLUE2};
  }
`;
