import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {RepositoryInformationFragment} from 'src/RepositoryInformation';
import {RepositorySelector} from 'src/types/globalTypes';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressFromPath} from 'src/workspace/repoAddressFromPath';
import {RepoAddress} from 'src/workspace/types';
import {InstanceExecutableQuery} from 'src/workspace/types/InstanceExecutableQuery';
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoriesOrError_PythonError,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes,
  RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location,
} from 'src/workspace/types/RootRepositoriesQuery';

export type Repository = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes;
export type RepositoryLocation = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location;
export type RepositoryError = RootRepositoriesQuery_repositoriesOrError_PythonError;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

const LAST_REPO_KEY = 'dagit.last-repo';

type WorkspaceState = {
  error: RepositoryError | null;
  loading: boolean;
  allRepos: DagsterRepoOption[];
  activeRepo: null | {
    repo: DagsterRepoOption;
    address: RepoAddress;
    path: string;
  };
  repoPath: string | null;
};

export const WorkspaceContext = React.createContext<WorkspaceState | null>(
  new Error('WorkspaceContext should never be uninitialized') as any,
);

export const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          pipelines {
            name
            pipelineSnapshotId
          }
          partitionSets {
            pipelineName
          }
          location {
            name
            isReloadSupported
            environmentPath
          }
          ...RepositoryInfoFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${RepositoryInformationFragment}
`;

const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

export const isRepositoryOptionEqual = (a: DagsterRepoOption, b: DagsterRepoOption) =>
  getRepositoryOptionHash(a) === getRepositoryOptionHash(b);

/**
 * useRepositoryOptions vends the set of available repositories by fetching them via GraphQL
 * and coercing the response to the DagsterRepoOption[] type.
 */
export const useRepositoryOptions = () => {
  const {data, loading} = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  let options: DagsterRepoOption[] = [];
  if (!data || !data.repositoriesOrError) {
    return {options, loading, error: null};
  }
  if (data.repositoriesOrError.__typename === 'PythonError') {
    return {options, loading, error: data.repositoriesOrError};
  }

  options = data.repositoriesOrError.nodes.map((repository) => ({
    repository,
    repositoryLocation: repository.location,
  }));

  return {error: null, loading, options};
};

/**
 * A hook that supplies the current workspace state of Dagit, including the current
 * "active" repo based on the URL or localStorage, all fetched repositories available
 * in the workspace, and loading/error state for the relevant query.
 */
export const useWorkspaceState = () => {
  const match = useRouteMatch<{repoPath: string}>(['/workspace/:repoPath']);
  const repoPath: string | null = match?.params?.repoPath || null;

  const repoAddress = repoPath ? repoAddressFromPath(repoPath) : null;
  const {options, loading, error} = useRepositoryOptions();
  const [localStorageRepo, setLocalStorageRepo] = useLocalStorageState(options);

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
    allRepos: options,
    activeRepo,
    repoPath,
  };
};

/**
 * useLocalStorageState vends `[repo, setRepo]` and internally mirrors the current
 * selection into localStorage so that the default selection in new browser windows
 * is the repo currently active in your session.
 */
const useLocalStorageState = (options: DagsterRepoOption[]) => {
  const [repoKey, setRepoKey] = React.useState<string | null>(null);

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

export const useRepositorySelector = (): RepositorySelector => {
  const repository = useRepository();
  return {
    repositoryLocationName: repository?.location.name || '',
    repositoryName: repository?.name || '',
  };
};

export const useRepository = () => {
  const workspaceState = React.useContext(WorkspaceContext);
  return workspaceState?.activeRepo?.repo.repository;
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

export const INSTANCE_EXECUTABLE_QUERY = gql`
  query InstanceExecutableQuery {
    instance {
      executablePath
    }
  }
`;

export const useDagitExecutablePath = () => {
  const {data} = useQuery<InstanceExecutableQuery>(INSTANCE_EXECUTABLE_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return data?.instance.executablePath;
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
