import {ColorsWIP} from '@dagster-io/ui';
import memoize from 'lodash/memoize';
import * as React from 'react';
import {useLocation} from 'react-router-dom';
import styled from 'styled-components/macro';

import {
  DagsterRepoOption,
  getRepositoryOptionHash,
  WorkspaceContext,
} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {FlatContentList} from './FlatContentList';
import {RepoNavItem} from './RepoNavItem';
import {RepoDetails} from './RepoSelector';
import {RepositoryLocationStateObserver} from './RepositoryLocationStateObserver';

export const HIDDEN_REPO_KEYS = 'dagit.hidden-repo-keys';

const buildDetails = memoize((option: DagsterRepoOption) => ({
  repoAddress: buildRepoAddress(option.repository.name, option.repositoryLocation.name),
  metadata: option.repository.displayMetadata,
}));

const hiddenKeysFromLocalStorage = () => {
  const keys = window.localStorage.getItem(HIDDEN_REPO_KEYS);
  if (keys) {
    const parsed = JSON.parse(keys);
    if (Array.isArray(parsed)) {
      return new Set(parsed);
    }
  }

  return new Set();
};

/**
 * useNavVisibleRepos vends `[reposForKeys, toggleRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
const useNavVisibleRepos = (
  options: DagsterRepoOption[],
): [typeof repoDetailsForKeys, typeof toggleRepo] => {
  // Initialize local state with an empty Set.
  const [visibleKeys, setVisibleKeys] = React.useState<Set<string>>(() => new Set());

  const allKeys = React.useMemo(() => options.map((option) => getRepositoryOptionHash(option)), [
    options,
  ]);

  // Collect hidden keys from localStorage and remove them from the visible repo key list.
  React.useEffect(() => {
    setVisibleKeys(() => {
      // If there's only one key, skip the local storage check -- we have to show this one.
      if (allKeys.length === 1) {
        return new Set(allKeys);
      }

      const hiddenKeys = hiddenKeysFromLocalStorage();
      const visible = allKeys.filter((key) => !hiddenKeys.has(key));

      if (visible.length) {
        return new Set(visible);
      }

      return new Set();
    });
  }, [allKeys]);

  const toggleRepo = React.useCallback((option: RepoDetails) => {
    const {repoAddress} = option;
    const key = `${repoAddress.name}:${repoAddress.location}`;

    setVisibleKeys((current) => {
      const copy = new Set([...Array.from(current || [])]);
      if (copy.has(key)) {
        copy.delete(key);
      } else {
        copy.add(key);
      }
      return copy;
    });
  }, []);

  // When the list of matching repos changes, update localStorage. Any repos in the
  // `options` list that are not marked as "visible" should be stored as "hidden".
  React.useEffect(() => {
    const hiddenKeys = hiddenKeysFromLocalStorage();
    allKeys.forEach((key) => {
      if (visibleKeys.has(key)) {
        hiddenKeys.delete(key);
      } else {
        hiddenKeys.add(key);
      }
    });
    window.localStorage.setItem(HIDDEN_REPO_KEYS, JSON.stringify(Array.from(hiddenKeys)));
  }, [allKeys, visibleKeys]);

  const repoDetailsForKeys = React.useMemo(() => {
    const visibleOptions = options.filter((o) => visibleKeys.has(getRepositoryOptionHash(o)));
    return new Set(visibleOptions.map(buildDetails));
  }, [options, visibleKeys]);

  return [repoDetailsForKeys, toggleRepo];
};

const LoadedRepositorySection: React.FC<{allRepos: DagsterRepoOption[]}> = ({allRepos}) => {
  const location = useLocation();
  const workspacePath = location.pathname.split('/workspace/').pop();
  const [, repoPath, , selector, tab] =
    workspacePath?.match(
      /([^\/]+)\/(pipelines|jobs|solids|ops|sensors|schedules)\/([^\/]+)\/?([^\/]+)?/,
    ) || [];

  const [visibleRepos, toggleRepo] = useNavVisibleRepos(allRepos);

  const visibleOptions = React.useMemo(() => {
    return Array.from(visibleRepos)
      .map((visible) => {
        const {repoAddress} = visible;
        return allRepos.find(
          (option) =>
            getRepositoryOptionHash(option) === `${repoAddress.name}:${repoAddress.location}`,
        );
      })
      .filter((option) => !!option) as DagsterRepoOption[];
  }, [allRepos, visibleRepos]);

  return (
    <Container>
      <ListContainer>
        {visibleRepos.size ? (
          <FlatContentList
            repoPath={repoPath}
            selector={selector}
            repos={visibleOptions}
            tab={tab}
          />
        ) : allRepos.length > 0 ? (
          <EmptyState>Select a repository to see a list of jobs and pipelines.</EmptyState>
        ) : (
          <EmptyState>
            There are no repositories in this workspace. Add a repository to see a list of jobs and
            pipelines.
          </EmptyState>
        )}
      </ListContainer>
      <RepositoryLocationStateObserver />
      <RepoNavItem
        allRepos={allRepos.map(buildDetails)}
        selected={visibleRepos}
        onToggle={toggleRepo}
      />
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
  const {allRepos, loading} = React.useContext(WorkspaceContext);

  if (loading) {
    return <div style={{flex: 1}} />;
  }

  return <LoadedRepositorySection allRepos={allRepos} />;
});
