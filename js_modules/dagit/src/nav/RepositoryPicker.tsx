import {Colors, Icon, Menu, MenuItem, Popover} from '@blueprintjs/core';
import React from 'react';
import {useHistory} from 'react-router';
import styled from 'styled-components/macro';

import {ReloadRepositoryLocationButton} from 'src/nav/ReloadRepositoryLocationButton';
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
          {repo.repository.name}
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
      <RepositoryPickerFlexContainer>
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
      </RepositoryPickerFlexContainer>
    </Popover>
  );
};

const RepoTitle = styled.div`
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.9;
  display: flex;
  align-items: center;
  height: 19px;
`;

const RepositoryPickerFlexContainer = styled.div`
  border-bottom: 1px solid ${Colors.DARK_GRAY4};
  padding: 10px 10px;
  display: flex;
  align-items: center;
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
