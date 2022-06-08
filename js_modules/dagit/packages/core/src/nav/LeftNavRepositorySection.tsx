import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {SectionedLeftNav} from '../ui/SectionedLeftNav';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {RepoNavItem} from './RepoNavItem';
import {RepositoryLocationStateObserver} from './RepositoryLocationStateObserver';

const LoadedRepositorySection: React.FC<{
  allRepos: DagsterRepoOption[];
  visibleRepos: DagsterRepoOption[];
  toggleVisible: (repoAddresses: RepoAddress[]) => void;
}> = ({allRepos, visibleRepos, toggleVisible}) => {
  const listContent = () => {
    if (visibleRepos.length) {
      return <SectionedLeftNav />;
    }

    if (allRepos.length > 0) {
      return <EmptyState>Select a repository to see a list of jobs.</EmptyState>;
    }

    return (
      <EmptyState>
        There are no repositories in this workspace. Add a repository to see a list of jobs.
      </EmptyState>
    );
  };

  return (
    <Container>
      <ListContainer>{listContent()}</ListContainer>
      <RepositoryLocationStateObserver />
      <RepoNavItem allRepos={allRepos} selected={visibleRepos} onToggle={toggleVisible} />
    </Container>
  );
};

const Container = styled.div`
  background: ${Colors.Gray100};
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
  color: ${Colors.Gray400};
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
