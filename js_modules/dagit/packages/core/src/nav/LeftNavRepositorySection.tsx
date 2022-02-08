import {ColorsWIP} from '@dagster-io/ui';
import * as React from 'react';
import {useLocation} from 'react-router-dom';
import styled from 'styled-components/macro';

import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {FlatContentList} from './FlatContentList';
import {RepoNavItem} from './RepoNavItem';
import {RepositoryLocationStateObserver} from './RepositoryLocationStateObserver';

const LoadedRepositorySection: React.FC<{
  allRepos: DagsterRepoOption[];
  visibleRepos: DagsterRepoOption[];
  toggleVisible: (repoAddress: RepoAddress) => void;
}> = ({allRepos, visibleRepos, toggleVisible}) => {
  const location = useLocation();
  const workspacePath = location.pathname.split('/workspace/').pop();
  const [, repoPath, , selector, tab] =
    workspacePath?.match(
      /([^\/]+)\/(pipelines|jobs|solids|ops|sensors|schedules)\/([^\/]+)\/?([^\/]+)?/,
    ) || [];

  return (
    <Container>
      <ListContainer>
        {visibleRepos.length ? (
          <FlatContentList repoPath={repoPath} selector={selector} repos={visibleRepos} tab={tab} />
        ) : allRepos.length > 0 ? (
          <EmptyState>Select a repository to see a list of jobs.</EmptyState>
        ) : (
          <EmptyState>
            There are no repositories in this workspace. Add a repository to see a list of jobs.
          </EmptyState>
        )}
      </ListContainer>
      <RepositoryLocationStateObserver />
      <RepoNavItem allRepos={allRepos} selected={visibleRepos} onToggle={toggleVisible} />
    </Container>
  );
};

const Container = styled.div`
  background: ${ColorsWIP.Gray100};
  display: flex;
  flex: 1;
  overflow: none;
  flex-direction: column;
  min-height: 0;
`;

const ListContainer = styled.div`
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
`;

const EmptyState = styled.div`
  color: ${ColorsWIP.Gray400};
  line-height: 20px;
  padding: 6px 24px 0;
`;

export const LeftNavRepositorySection = React.memo(() => {
  const {allRepos, loading, visibleRepos, toggleVisible} = React.useContext(WorkspaceContext);

  if (loading) {
    return <div style={{flex: 1}} />;
  }

  return (
    <LoadedRepositorySection
      allRepos={allRepos}
      visibleRepos={visibleRepos}
      toggleVisible={toggleVisible}
    />
  );
});
