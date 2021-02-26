import {Icon, Colors, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {ShortcutHandler} from 'src/app/ShortcutHandler';
import {featureEnabled, FeatureFlag} from 'src/app/Util';
import {useRepositoryLocationReload} from 'src/nav/ReloadRepositoryLocationButton';
import {Box} from 'src/ui/Box';
import {Spinner} from 'src/ui/Spinner';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export const RepositoryLink: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {location} = repoAddress;
  const {reloading, onClick} = useRepositoryLocationReload(repoAddress.location);

  return (
    <Box flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}}>
      <RepositoryName
        to={workspacePathFromAddress(repoAddress)}
        title={repoAddressAsString(repoAddress)}
      >
        {repoAddressAsString(repoAddress)}
      </RepositoryName>
      <ShortcutHandler
        onShortcut={onClick}
        shortcutLabel={`⌥R`}
        shortcutFilter={(e) => e.keyCode === 82 && e.altKey && featureEnabled(FeatureFlag.LeftNav)}
      >
        <ReloadTooltip content={reloading ? 'Reloading…' : `Reload location ${location}`}>
          {reloading ? (
            <Spinner purpose="body-text" />
          ) : (
            <StyledButton onClick={onClick}>
              <Icon icon="refresh" iconSize={11} color={Colors.GRAY2} />
            </StyledButton>
          )}
        </ReloadTooltip>
      </ShortcutHandler>
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
