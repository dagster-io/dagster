import {ApolloQueryResult, gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {useRouteMatch} from 'react-router-dom';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';

import {REPOSITORY_INFO_FRAGMENT} from './RepositoryInformation';
import {buildRepoAddress} from './buildRepoAddress';
import {findRepoContainingPipeline} from './findRepoContainingPipeline';
import {RepoAddress} from './types';
import {
  RootRepositoriesQuery,
  RootRepositoriesQuery_repositoryLocationsOrError_PythonError,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation,
  RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories,
} from './types/RootRepositoriesQuery';

type Repository = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories;
type RepositoryLocation = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation;
type RepositoryLocationNode = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes;
type RepositoryError = RootRepositoriesQuery_repositoryLocationsOrError_PythonError;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

type WorkspaceState = {
  error: RepositoryError | null;
  loading: boolean;
  locations: RepositoryLocationNode[];
  allRepos: DagsterRepoOption[];
  refetch: () => Promise<ApolloQueryResult<RootRepositoriesQuery>>;
};

export const WorkspaceContext = React.createContext<WorkspaceState>(
  new Error('WorkspaceContext should never be uninitialized') as any,
);

const ROOT_REPOSITORIES_QUERY = gql`
  query RootRepositoriesQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          __typename
          ... on RepositoryLocation {
            id
            isReloadSupported
            serverId
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
                id
                pipelineName
              }
              ...RepositoryInfoFragment
            }
          }
          ... on RepositoryLocationLoadFailure {
            id
            name
            error {
              ...PythonErrorFragment
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
`;

export const REPOSITORY_LOCATIONS_FRAGMENT = gql`
  fragment RepositoryLocationsFragment on RepositoryLocationsOrError {
    __typename
    ... on RepositoryLocationConnection {
      nodes {
        __typename
        ... on RepositoryLocation {
          id
          isReloadSupported
          serverId
          name
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
  ${PYTHON_ERROR_FRAGMENT}
`;

export const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

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

  return {
    refetch,
    loading,
    error,
    locations,
    allRepos: options,
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

export const useRepository = (repoAddress: RepoAddress) => {
  const {options} = useRepositoryOptions();
  return options.find(
    (option) =>
      option.repository.name === repoAddress.name &&
      option.repositoryLocation.name === repoAddress.location,
  );
};

export const useActivePipelineForName = (pipelineName: string, snapshotId?: string) => {
  const {options} = useRepositoryOptions();
  const reposWithMatch = findRepoContainingPipeline(options, pipelineName, snapshotId);
  if (reposWithMatch.length) {
    const match = reposWithMatch[0];
    return match.repository.pipelines.find((pipeline) => pipeline.name === pipelineName) || null;
  }
  return null;
};

export const usePipelineSelector = (
  repoAddress: RepoAddress | null,
  pipelineName: string,
  solidSelection?: string[],
) => {
  const repositorySelector = {
    repositoryName: repoAddress?.name || '',
    repositoryLocationName: repoAddress?.location || '',
  };

  return {
    ...repositorySelector,
    pipelineName,
    solidSelection,
  };
};

export const optionToRepoAddress = (option: DagsterRepoOption) =>
  buildRepoAddress(option.repository.name, option.repository.location.name);
