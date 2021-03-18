import {Colors, Icon} from '@blueprintjs/core';
import {Popover2 as Popover, Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ShortcutHandler} from 'src/app/ShortcutHandler';
import {featureEnabled, FeatureFlag} from 'src/app/Util';
import {useRepositoryLocationReload} from 'src/nav/ReloadRepositoryLocationButton';
import {RepoDetails, RepoSelector} from 'src/nav/RepoSelector';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Spinner} from 'src/ui/Spinner';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  allRepos: RepoDetails[];
  selected: Set<RepoDetails>;
  onToggle: (repoAddress: RepoDetails) => void;
}

export const RepoNavItem: React.FC<Props> = (props) => {
  const {allRepos, selected, onToggle} = props;

  const summary = () => {
    if (allRepos.length === 0) {
      return <span style={{color: Colors.GRAY1}}>No repositories</span>;
    }
    if (allRepos.length === 1 || selected.size === 1) {
      return <SingleRepoSummary repoAddress={allRepos[0].repoAddress} />;
    }
    return (
      <span style={{color: Colors.LIGHT_GRAY3, fontWeight: 500}}>
        {`Showing ${selected.size} of ${allRepos.length}`}
      </span>
    );
  };

  return (
    <Box
      background={Colors.DARK_GRAY2}
      padding={{vertical: 8, horizontal: 12}}
      flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
    >
      <Group direction="column" spacing={2}>
        <div style={{color: Colors.GRAY3, fontSize: '11px', textTransform: 'uppercase'}}>
          Repository
        </div>
        {summary()}
      </Group>
      {allRepos.length > 1 ? (
        <Popover
          canEscapeKeyClose
          interactionKind="click"
          modifiers={{offset: {enabled: true, options: {offset: [0, 24]}}}}
          placement="right"
          popoverClassName="bp3-dark"
          content={
            <Box padding={16} style={{maxWidth: '500px', borderRadius: '3px'}}>
              <RepoSelector options={allRepos} onToggle={onToggle} selected={selected} />
            </Box>
          }
        >
          <ButtonLink color={Colors.GRAY5} underline="hover">
            <span style={{fontSize: '13px'}}>Filter</span>
          </ButtonLink>
        </Popover>
      ) : null}
    </Box>
  );
};

const SingleRepoSummary: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {reloading, onClick} = useRepositoryLocationReload(repoAddress.location);
  return (
    <Group direction="row" spacing={8} alignItems="center">
      <SingleRepoNameLink to={workspacePathFromAddress(repoAddress)}>
        {repoAddress.name}
      </SingleRepoNameLink>
      <ShortcutHandler
        onShortcut={() => {}}
        shortcutLabel={`⌥R`}
        shortcutFilter={(e) => e.keyCode === 82 && e.altKey && featureEnabled(FeatureFlag.LeftNav)}
      >
        <Tooltip content={reloading ? 'Reloading…' : `Reload location ${location}`}>
          {reloading ? (
            <Spinner purpose="body-text" />
          ) : (
            <StyledButton onClick={onClick}>
              <Icon icon="refresh" iconSize={11} color={Colors.GRAY4} />
            </StyledButton>
          )}
        </Tooltip>
      </ShortcutHandler>
    </Group>
  );
};

const SingleRepoNameLink = styled(Link)`
  color: Colors.LIGHT_GRAY3,
  max-width: 190px;
  overflow-x: hidden;
  text-overflow: ellipsis;

  && {
    color: ${Colors.LIGHT_GRAY3};
    font-weight: 500;
  }

  && :hover, &&:active {
    color: ${Colors.LIGHT_GRAY1};
  }
`;

const StyledButton = styled.button`
  background-color: transparent;
  border: 0;
  cursor: pointer;
  padding: 0;
  margin: 0;
  position: relative;
  top: 1px;

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
    fill: ${Colors.BLUE5};
  }
`;
