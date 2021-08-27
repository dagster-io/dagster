import {Button, Colors, Icon, Menu, MenuItem, Popover} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';
import {RepositoryInformation} from '../workspace/RepositoryInformation';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoPath} from '../workspace/buildRepoAddress';

import {ReloadRepositoryLocationButton} from './ReloadRepositoryLocationButton';

interface RepositoryPickerProps {
  loading: boolean;
  options: DagsterRepoOption[];
  selected: DagsterRepoOption[];
  toggleRepo: (option: DagsterRepoOption) => void;
}

export const RepositoryPicker: React.FC<RepositoryPickerProps> = (props) => {
  const history = useHistory();
  const {loading, options, selected, toggleRepo} = props;
  const [open, setOpen] = React.useState(false);

  const titleContents = () => {
    if (selected.length) {
      const repo = selected[0];
      return (
        <>
          <span style={{overflow: 'hidden', textOverflow: 'ellipsis'}} title={repo.repository.name}>
            {repo.repository.name}
          </span>
          <Icon icon="caret-down" style={{opacity: 0.9, marginLeft: 3}} />
        </>
      );
    }

    if (loading) {
      return <Spinner purpose="body-text" />;
    }

    return <NoReposFound>No repositories found</NoReposFound>;
  };

  return (
    <Popover
      fill={true}
      isOpen={open && options.length > 0}
      onInteraction={setOpen}
      canEscapeKeyClose
      minimal
      position="bottom-left"
      content={
        <Menu style={{minWidth: 280}}>
          {options.map((option, idx) => (
            <MenuItem
              key={idx}
              onClick={() => {
                toggleRepo(option);
                history.push(
                  `/workspace/${buildRepoPath(
                    option.repository.name,
                    option.repositoryLocation.name,
                  )}`,
                );
              }}
              active={selected.includes(option)}
              icon="git-repo"
              text={<RepositoryInformation repository={option.repository} />}
            />
          ))}
        </Menu>
      }
    >
      <Container
        padding={{vertical: 8, horizontal: 12}}
        border={{width: 1, side: 'bottom', color: Colors.DARK_GRAY4}}
        flex={{alignItems: 'center'}}
      >
        <div style={{flex: 1, minWidth: 0}}>
          <div
            style={{
              fontSize: 10.5,
              color: Colors.GRAY1,
              userSelect: 'none',
              textTransform: 'uppercase',
            }}
          >
            Repository
          </div>
          <RepoTitle>{titleContents()}</RepoTitle>
        </div>
        <ReloadRepositoryLocationButton
          location={
            selected
              .filter((option) => option.repositoryLocation.isReloadSupported)
              .map((option) => option.repositoryLocation.name)[0]
          }
        >
          {({tryReload, reloading}) => (
            <ShortcutHandler
              onShortcut={tryReload}
              shortcutLabel={`⌥R`}
              shortcutFilter={(e) => e.keyCode === 82 && e.altKey}
            >
              <Tooltip
                className="bp3-dark"
                hoverOpenDelay={500}
                hoverCloseDelay={0}
                content="Reload metadata from this repository location."
              >
                <Button
                  icon={
                    reloading ? (
                      <Spinner purpose="body-text" />
                    ) : (
                      <Icon icon="refresh" iconSize={12} />
                    )
                  }
                  disabled={reloading}
                  onClick={tryReload}
                />
              </Tooltip>
            </ShortcutHandler>
          )}
        </ReloadRepositoryLocationButton>
      </Container>
    </Popover>
  );
};

const RepoTitle = styled.div`
  opacity: 0.9;
  display: flex;
  align-items: center;
  height: 19px;
  padding-right: 2px;
`;

const Container = styled(Box)`
  cursor: default;
  &:hover {
    background: ${Colors.BLACK};
  }
`;

const NoReposFound = styled.div`
  color: ${Colors.GRAY3};
  font-size: 12px;
  margin-top: 8px;
`;
