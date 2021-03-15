import {ApolloConsumer} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import memoize from 'lodash/memoize';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {JobsList} from 'src/nav/JobsList';
import {RepoNavItem} from 'src/nav/RepoNavItem';
import {RepoDetails} from 'src/nav/RepoSelector';
import {RepositoryContentList} from 'src/nav/RepositoryContentList';
import {RepositoryLocationStateObserver} from 'src/nav/RepositoryLocationStateObserver';
import {
  DagsterRepoOption,
  getRepositoryOptionHash,
  WorkspaceContext,
} from 'src/workspace/WorkspaceContext';
import {buildRepoAddress} from 'src/workspace/buildRepoAddress';

export const LAST_REPO_KEY = 'dagit.last-repo';
export const REPO_KEYS = 'dagit.repo-keys';

const buildDetails = memoize((option: DagsterRepoOption) => ({
  repoAddress: buildRepoAddress(option.repository.name, option.repositoryLocation.name),
  metadata: option.repository.displayMetadata,
}));

/**
 * useNavVisibleRepos vends `[reposForKeys, toggleRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
const useNavVisibleRepos = (
  options: DagsterRepoOption[],
): [typeof repoDetailsForKeys, typeof toggleRepo] => {
  const [repoKeys, setRepoKeys] = React.useState<Set<string> | null>(() => {
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

    return null;
  });

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

  const reposForKeys = React.useMemo(() => {
    if (!options.length) {
      return options;
    }

    if (!repoKeys) {
      return options.slice(0, 1);
    }

    const filtered = options.filter((o) => repoKeys.has(getRepositoryOptionHash(o)));
    if (filtered.length) {
      return filtered;
    }

    // If no matches for localStorage repo keys, just return the first one in the list.
    return options.slice(0, 1);
  }, [options, repoKeys]);

  const repoDetailsForKeys = React.useMemo(() => new Set(reposForKeys.map(buildDetails)), [
    reposForKeys,
  ]);

  React.useEffect(() => {
    window.localStorage.setItem(REPO_KEYS, JSON.stringify(Array.from(repoKeys || new Set())));
  }, [repoKeys]);

  return [repoDetailsForKeys, toggleRepo];
};

export const LeftNavRepositorySection = () => {
  const match = useRouteMatch<
    | {repoPath: string; selector: string; tab: string; rootTab: undefined}
    | {selector: undefined; tab: undefined; rootTab: string}
  >([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
    '/workspace/:repoPath/solids/:selector',
    '/workspace/:repoPath/schedules/:selector',
    '/:rootTab?',
  ]);

  const {allRepos} = React.useContext(WorkspaceContext);
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
    <div
      className="bp3-dark"
      style={{
        background: `rgba(0,0,0,0.3)`,
        color: Colors.WHITE,
        display: 'flex',
        flex: 1,
        overflow: 'none',
        flexDirection: 'column',
        minHeight: 0,
      }}
    >
      <RepoNavItem
        allRepos={allRepos.map(buildDetails)}
        selected={visibleRepos}
        onToggle={toggleRepo}
      />
      <ApolloConsumer>
        {(client) => <RepositoryLocationStateObserver client={client} />}
      </ApolloConsumer>
      {visibleRepos.size ? (
        <div style={{display: 'flex', flex: 1, flexDirection: 'column', minHeight: 0}}>
          <RepositoryContentList {...match?.params} repos={visibleOptions} />
          <JobsList {...match?.params} repos={visibleOptions} />
        </div>
      ) : null}
    </div>
  );
};
