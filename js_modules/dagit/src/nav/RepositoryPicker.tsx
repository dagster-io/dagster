import {Colors, Icon, Menu, MenuItem, Popover} from '@blueprintjs/core';
import React from 'react';
import {useHistory} from 'react-router';
import styled from 'styled-components/macro';

import {ReloadRepositoryLocationButton} from 'src/nav/ReloadRepositoryLocationButton';
import {Box} from 'src/ui/Box';
import {Spinner} from 'src/ui/Spinner';
import {RepositoryInformation} from 'src/workspace/RepositoryInformation';
import {DagsterRepoOption, isRepositoryOptionEqual} from 'src/workspace/WorkspaceContext';
import {workspacePath} from 'src/workspace/workspacePath';

interface RepositoryPickerProps {
  loading: boolean;
  options: DagsterRepoOption[];
  repo: DagsterRepoOption | null;
}

export const RepositoryPicker: React.FC<RepositoryPickerProps> = ({loading, repo, options}) => {
  const history = useHistory();
  const [open, setOpen] = React.useState(false);

  const selectOption = (repo: DagsterRepoOption) => {
    history.push(workspacePath(repo.repository.name, repo.repositoryLocation.name));
  };

  const titleContents = () => {
    if (repo) {
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
      isOpen={open}
      onInteraction={setOpen}
      minimal
      position="bottom-left"
      content={
        <Menu style={{minWidth: 280}}>
          {options.map((option, idx) => (
            <MenuItem
              key={idx}
              onClick={() => selectOption(option)}
              active={repo ? isRepositoryOptionEqual(repo, option) : false}
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
        {repo?.repositoryLocation.isReloadSupported && (
          <ReloadRepositoryLocationButton location={repo.repositoryLocation.name} />
        )}
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
