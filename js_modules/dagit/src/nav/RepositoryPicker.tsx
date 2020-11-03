import {
  Button,
  Classes,
  Colors,
  Dialog,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
} from '@blueprintjs/core';
import React from 'react';
import {useHistory} from 'react-router';
import styled from 'styled-components/macro';

import {
  DagsterRepoOption,
  isRepositoryOptionEqual,
  useDagitExecutablePath,
} from 'src/DagsterRepositoryContext';
import {RepositoryInformation} from 'src/RepositoryInformation';
import {ReloadRepositoryLocationButton, ReloadResult} from 'src/nav/ReloadRepositoryLocationButton';
import {FontFamily} from 'src/ui/styles';

interface RepositoryPickerProps {
  loading: boolean;
  options: DagsterRepoOption[];
  repo: DagsterRepoOption | null;
  setRepo: (repo: DagsterRepoOption) => void;
}

type LoadingError = {
  location: string;
  message: string;
};

export const RepositoryPicker: React.FC<RepositoryPickerProps> = ({
  loading,
  repo,
  setRepo,
  options,
}) => {
  const history = useHistory();
  const [open, setOpen] = React.useState(false);
  const [error, setError] = React.useState<LoadingError | null>(null);
  const [showErrorMessage, setShowErrorMessage] = React.useState(false);
  const dagitExecutablePath = useDagitExecutablePath();

  const selectOption = (repo: DagsterRepoOption) => {
    setRepo(repo);
    history.push('/');
  };

  const onReload = (location: string, result: ReloadResult) => {
    if (result.type === 'error') {
      setError({location, message: result.message});
    } else {
      setError(null);
    }
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
      return <Spinner size={16} />;
    }

    return <NoReposFound>No repositories found</NoReposFound>;
  };

  return (
    <>
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
                text={
                  <RepositoryInformation
                    repository={option.repository}
                    dagitExecutablePath={dagitExecutablePath}
                  />
                }
              />
            ))}
          </Menu>
        }
      >
        <RepositoryPickerFlexContainer>
          <div style={{flex: 1, minWidth: 0}}>
            <div style={{fontSize: 10.5, color: Colors.GRAY1, userSelect: 'none'}}>REPOSITORY</div>
            <RepoTitle>{titleContents()}</RepoTitle>
          </div>
          {repo?.repositoryLocation.isReloadSupported && (
            <ReloadRepositoryLocationButton
              location={repo.repositoryLocation.name}
              onReload={onReload}
            />
          )}
        </RepositoryPickerFlexContainer>
      </Popover>
      {error ? (
        <>
          <LoadingError onClick={() => setShowErrorMessage(true)}>
            <div style={{marginRight: '8px'}}>Error loading repository!</div>
            <Icon icon="info-sign" iconSize={14} color={Colors.DARK_GRAY3} />
          </LoadingError>
          <Dialog
            isOpen={showErrorMessage}
            title="Error loading repository"
            onClose={() => setShowErrorMessage(false)}
            style={{width: '700px'}}
          >
            <div className={Classes.DIALOG_BODY}>
              <div style={{marginBottom: '12px'}}>
                Failed to load repository location <strong>{error?.location}</strong>. Try again
                after resolving the issue below.
              </div>
              <Trace>{error?.message}</Trace>
            </div>
            <div className={Classes.DIALOG_FOOTER}>
              <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                <Button intent="primary" onClick={() => setShowErrorMessage(false)}>
                  OK
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      ) : null}
    </>
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

const LoadingError = styled.button`
  align-items: center;
  background-color: ${Colors.GOLD5};
  border: 0;
  color: ${Colors.DARK_GRAY3};
  cursor: pointer;
  display: flex;
  flex-direction: row;
  padding: 8px 12px;

  &:active {
    outline: none;
  }
`;

const Trace = styled.div`
  background-color: ${Colors.LIGHT_GRAY1};
  color: rgb(41, 50, 56);
  font-family: ${FontFamily.monospace};
  font-size: 12px;
  max-height: 60vh;
  overflow: auto;
  white-space: pre;
  padding: 16px;
`;
