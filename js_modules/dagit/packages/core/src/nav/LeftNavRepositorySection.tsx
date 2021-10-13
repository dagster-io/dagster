import memoize from 'lodash/memoize';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
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

export const LAST_REPO_KEY = 'dagit.last-repo';
export const REPO_KEYS = 'dagit.repo-keys';

const buildDetails = memoize((option: DagsterRepoOption) => ({
  repoAddress: buildRepoAddress(option.repository.name, option.repositoryLocation.name),
  metadata: option.repository.displayMetadata,
}));

const keysFromLocalStorage = () => {
  const keys = window.localStorage.getItem(REPO_KEYS);
  if (keys) {
    const parsed: string[] = JSON.parse(keys);
    return new Set(parsed);
  }

  // todo dish: Temporary while migrating to support filtering on multiple repos in
  // left nav.
  const key = window.localStorage.getItem(LAST_REPO_KEY);
  if (key) {
    return new Set([key]);
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
  const [repoKeys, setRepoKeys] = React.useState<Set<string>>(() => new Set());

  // Collect keys from localStorage. Any keys that are present in our option list will be pushed into
  // local state. If there are none specified in localStorage, just grab the first option.
  React.useEffect(() => {
    setRepoKeys(() => {
      const keys = keysFromLocalStorage();
      const hashes = options.map((option) => getRepositoryOptionHash(option));
      const matches = hashes.filter((hash) => keys.has(hash));

      if (matches.length) {
        return new Set(matches);
      }

      if (hashes.length) {
        return new Set([hashes[0]]);
      }

      return new Set();
    });
  }, [options]);

  const toggleRepo = React.useCallback((option: RepoDetails) => {
    const {repoAddress} = option;
    const key = `${repoAddress.name}:${repoAddress.location}`;

    setRepoKeys((current) => {
      const copy = new Set([...Array.from(current || [])]);
      if (copy.has(key)) {
        copy.delete(key);
      } else {
        copy.add(key);
      }
      return copy;
    });
  }, []);

  const reposForKeys = React.useMemo(
    () => options.filter((o) => repoKeys.has(getRepositoryOptionHash(o))),
    [options, repoKeys],
  );

  // When the list of matching repos changes, update localStorage.
  React.useEffect(() => {
    const foundKeys = reposForKeys.map((option) => getRepositoryOptionHash(option));
    window.localStorage.setItem(REPO_KEYS, JSON.stringify(foundKeys));
  }, [reposForKeys]);

  const repoDetailsForKeys = React.useMemo(() => new Set(reposForKeys.map(buildDetails)), [
    reposForKeys,
  ]);

  return [repoDetailsForKeys, toggleRepo];
};

const LoadedRepositorySection: React.FC<{allRepos: DagsterRepoOption[]}> = ({allRepos}) => {
  const match = useRouteMatch<
    | {repoPath: string; selector: string; tab: string; rootTab: undefined}
    | {selector: undefined; tab: undefined; rootTab: string}
  >([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
    '/workspace/:repoPath/jobs/:selector/:tab?',
    '/workspace/:repoPath/solids/:selector',
    '/workspace/:repoPath/schedules/:selector',
    '/workspace/:repoPath/sensors/:selector',
    '/:rootTab?',
  ]);

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
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 8}}
          padding={{horizontal: 24, bottom: 12}}
        >
          <IconWIP name="job" />
          <span style={{fontSize: '16px', fontWeight: 600}}>Jobs and pipelines</span>
        </Box>
        {visibleRepos.size ? (
          <FlatContentList {...match?.params} repos={visibleOptions} />
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
