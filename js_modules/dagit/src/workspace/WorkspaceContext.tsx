import {ApolloQueryResult, gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT} from 'src/RepositoryInformation';
import {RepositorySelector} from 'src/types/globalTypes';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressFromPath} from 'src/workspace/repoAddressFromPath';
import {RepoAddress} from 'src/workspace/types';
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoryLocationsOrError_PythonError,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories,
} from 'src/workspace/types/RootRepositoriesQuery';

type Repository = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories;
type RepositoryLocation = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation;
type RepositoryLocationNode = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes;
type RepositoryError = RootRepositoriesQuery_repositoryLocationsOrError_PythonError;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

export const LAST_REPO_KEY = 'dagit.last-repo';

type WorkspaceState = {
  error: RepositoryError | null;
  loading: boolean;
  locations: RepositoryLocationNode[];
  allRepos: DagsterRepoOption[];
  activeRepo: null | {
    repo: DagsterRepoOption;
    address: RepoAddress;
    path: string;
  };
  refetch: () => Promise<ApolloQueryResult<RootRepositoriesQuery>>;
  repoPath: string | null;
};

export const WorkspaceContext = React.createContext<WorkspaceState>(
  new Error('WorkspaceContext should never be uninitialized') as any,
);

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          __typename
          ... on RepositoryLocation {
            id
            isReloadSupported
            name
            repositories {
              id
              name
              pipelines {
                id
                name
                pipelineSnapshotId
              }
              partitionSets {
                pipelineName
              }
              ...RepositoryInfoFragment
            }
          }
          ... on RepositoryLocationLoadFailure {
            id
            name
            error {
              message
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_INFO_FRAGMENT}
`;

const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

export const isRepositoryOptionEqual = (a: DagsterRepoOption, b: DagsterRepoOption) =>
  getRepositoryOptionHash(a) === getRepositoryOptionHash(b);

/**
 * useLocalStorageState vends `[repo, setRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
const useLocalStorageState = (options: DagsterRepoOption[]) => {
  const [repoKey, setRepoKey] = React.useState<string | null>(() =>
    window.localStorage.getItem(LAST_REPO_KEY),
  );

  const setRepo = (next: DagsterRepoOption) => {
    const key = getRepositoryOptionHash(next);
    window.localStorage.setItem(LAST_REPO_KEY, key);
    setRepoKey(key);
  };

  // If the selection is null or the selected repository cannot be found in the set,
  // coerce the selection to the last used repo or [0].
  React.useEffect(() => {
    if (
      options.length &&
      (!repoKey || !options.some((o) => getRepositoryOptionHash(o) === repoKey))
    ) {
      const lastKey = window.localStorage.getItem(LAST_REPO_KEY);
      const last = lastKey && options.find((o) => getRepositoryOptionHash(o) === lastKey);
      setRepoKey(getRepositoryOptionHash(last || options[0]));
    }
  }, [repoKey, options]);

  const repoForKey = options.find((o) => getRepositoryOptionHash(o) === repoKey) || null;
  return [repoForKey, setRepo] as [typeof repoForKey, typeof setRepo];
};

/**
 * A hook that supplies the current workspace state of Dagit, including the current
 * "active" repo based on the URL or localStorage, all fetched repositories available
 * in the workspace, and loading/error state for the relevant query.
 */
const useWorkspaceState = () => {
  const match = useRouteMatch<{repoPath: string}>(['/workspace/:repoPath']);
  const repoPath: string | null = match?.params?.repoPath || null;

  const {data, loading, refetch} = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const locations = React.useMemo(() => {
    return data?.repositoryLocationsOrError.__typename === 'RepositoryLocationConnection'
      ? data?.repositoryLocationsOrError.nodes
      : [];
  }, [data]);

  const {options, error} = React.useMemo(() => {
    let options: DagsterRepoOption[] = [];
    if (!data || !data.repositoryLocationsOrError) {
      return {options, error: null};
    }
    if (data.repositoryLocationsOrError.__typename === 'PythonError') {
      return {options, error: data.repositoryLocationsOrError};
    }

    options = data.repositoryLocationsOrError.nodes.reduce((accum, repositoryLocation) => {
      if (repositoryLocation.__typename === 'RepositoryLocationLoadFailure') {
        return accum;
      }
      const reposForLocation = repositoryLocation.repositories.map((repository) => {
        return {repository, repositoryLocation};
      });
      return [...accum, ...reposForLocation];
    }, []);

    return {error: null, options};
  }, [data]);

  const [localStorageRepo, setLocalStorageRepo] = useLocalStorageState(options);

  const repoAddress = React.useMemo(() => (repoPath ? repoAddressFromPath(repoPath) : null), [
    repoPath,
  ]);

  // If a repo is identified in the current route and that repo has been loaded,
  // that's our `repoForPath`. It takes priority as the "active" repo.
  const repoForPath = React.useMemo(() => {
    if (options && !loading && !error && repoAddress) {
      const {name, location} = repoAddress;
      return (
        options.find(
          (option) =>
            option.repository.name === name && option.repositoryLocation.name === location,
        ) || null
      );
    }
    return null;
  }, [error, loading, options, repoAddress]);

  // If there is no `repoForPath`, fall back to the local storage state, typically as set by the
  // left nav. If that doesn't exist either, just default to the first available repo.
  const activeRepo = React.useMemo(() => {
    const repo = repoForPath || localStorageRepo || options[0] || null;
    if (!repo) {
      return null;
    }
    const address = {name: repo.repository.name, location: repo.repositoryLocation.name};
    const path = repoAddressAsString(address);
    return {repo, address, path};
  }, [localStorageRepo, options, repoForPath]);

  // Update local storage with the latest active repo.
  React.useEffect(() => {
    if (activeRepo?.repo && activeRepo.repo !== localStorageRepo) {
      setLocalStorageRepo(activeRepo.repo);
    }
  }, [activeRepo, localStorageRepo, setLocalStorageRepo]);

  return {
    loading,
    error,
    locations,
    allRepos: options,
    activeRepo,
    refetch,
    repoPath,
  };
};

export const WorkspaceProvider: React.FC = (props) => {
  const {children} = props;
  const workspaceState = useWorkspaceState();
  return <WorkspaceContext.Provider value={workspaceState}>{children}</WorkspaceContext.Provider>;
};

export const useRepositoryOptions = () => {
  const {allRepos: options, loading, error} = React.useContext(WorkspaceContext);
  return {options, loading, error};
};

export const useActiveRepo = () => {
  const {activeRepo} = React.useContext(WorkspaceContext);
  return activeRepo;
};

export const useRepository = () => {
  const {activeRepo} = React.useContext(WorkspaceContext);
  return activeRepo?.repo.repository;
};

export const useRepositorySelector = (): RepositorySelector => {
  const repository = useRepository();
  return {
    repositoryLocationName: repository?.location.name || '',
    repositoryName: repository?.name || '',
  };
};

export const useActivePipelineForName = (pipelineName: string) => {
  const repository = useRepository();
  return repository?.pipelines.find((pipeline) => pipeline.name === pipelineName) || null;
};

export const usePipelineSelector = (pipelineName: string, solidSelection?: string[]) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    pipelineName,
    solidSelection,
  };
};

export const useScheduleSelector = (scheduleName: string) => {
  const repositorySelector = useRepositorySelector();
  return {
    ...repositorySelector,
    scheduleName,
  };
};

export const optionToRepoAddress = (option: DagsterRepoOption) => {
  return {
    name: option.repository.name,
    location: option.repository.location.name,
  };
};

export const scheduleSelectorWithRepository = (
  scheduleName: string,
  repositorySelector?: RepositorySelector,
) => {
  return {
    ...repositorySelector,
    scheduleName,
  };
};
