import {ApolloQueryResult, gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {PipelineSelector} from '../types/globalTypes';

import {REPOSITORY_INFO_FRAGMENT} from './RepositoryInformation';
import {buildRepoAddress} from './buildRepoAddress';
import {findRepoContainingPipeline} from './findRepoContainingPipeline';
import {RepoAddress} from './types';
import {
  RootWorkspaceQuery,
  RootWorkspaceQuery_workspaceOrError_PythonError,
  RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries,
  RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation,
  RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories,
  RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors,
  RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules,
} from './types/RootWorkspaceQuery';

type Repository = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories;
type RepositoryLocation = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation;
type RepositoryError = RootWorkspaceQuery_workspaceOrError_PythonError;

export type WorkspaceJobSensor = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors;
export type WorkspaceJobSchedule = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules;
export type WorkspaceRepositoryLocationNode = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries;

export interface DagsterRepoOption {
  repositoryLocation: RepositoryLocation;
  repository: Repository;
}

export type WorkspaceState = {
  error: RepositoryError | null;
  loading: boolean;
  locationEntries: WorkspaceRepositoryLocationNode[];
  allRepos: DagsterRepoOption[];
  refetch: () => Promise<ApolloQueryResult<RootWorkspaceQuery>>;
};

export const WorkspaceContext = React.createContext<WorkspaceState>(
  new Error('WorkspaceContext should never be uninitialized') as any,
);

const ROOT_WORKSPACE_QUERY = gql`
  query RootWorkspaceQuery {
    workspaceOrError {
      __typename
      ... on Workspace {
        locationEntries {
          __typename
          id
          name
          loadStatus
          displayMetadata {
            key
            value
          }
          updatedTimestamp
          locationOrLoadError {
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
                  isJob
                  graphName
                  pipelineSnapshotId
                  modes {
                    id
                    name
                  }
                  schedules {
                    id
                    mode
                    name
                    scheduleState {
                      id
                      status
                    }
                  }
                  sensors {
                    id
                    name
                    targets {
                      mode
                      pipelineName
                    }
                    sensorState {
                      id
                      status
                    }
                  }
                }
                partitionSets {
                  id
                  mode
                  pipelineName
                }
                ...RepositoryInfoFragment
              }
            }
            ... on PythonError {
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

export const getRepositoryOptionHash = (a: DagsterRepoOption) =>
  `${a.repository.name}:${a.repositoryLocation.name}`;

/**
 * A hook that supplies the current workspace state of Dagit, including the current
 * "active" repo based on the URL or localStorage, all fetched repositories available
 * in the workspace, and loading/error state for the relevant query.
 */
const useWorkspaceState = () => {
  const {data, loading, refetch} = useQuery<RootWorkspaceQuery>(ROOT_WORKSPACE_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const workspaceOrError = data?.workspaceOrError;

  const locationEntries = React.useMemo(
    () => (workspaceOrError?.__typename === 'Workspace' ? workspaceOrError.locationEntries : []),
    [workspaceOrError],
  );

  const {options, error} = React.useMemo(() => {
    let options: DagsterRepoOption[] = [];
    if (!workspaceOrError) {
      return {options, error: null};
    }

    if (workspaceOrError.__typename === 'PythonError') {
      return {options, error: workspaceOrError};
    }

    options = workspaceOrError.locationEntries.reduce((accum, locationEntry) => {
      if (locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
        return accum;
      }
      const repositoryLocation = locationEntry.locationOrLoadError;
      const reposForLocation = repositoryLocation.repositories.map((repository) => {
        return {repository, repositoryLocation};
      });
      return [...accum, ...reposForLocation];
    }, [] as DagsterRepoOption[]);

    return {error: null, options};
  }, [workspaceOrError]);

  return {
    refetch,
    loading: loading && !data, // Only "loading" on initial load.
    error,
    locationEntries,
    allRepos: options,
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

export const useRepository = (repoAddress: RepoAddress | null) => {
  const {options} = useRepositoryOptions();
  return findRepositoryAmongOptions(options, repoAddress) || null;
};

export const findRepositoryAmongOptions = (
  options: DagsterRepoOption[],
  repoAddress: RepoAddress | null,
) => {
  return repoAddress
    ? options.find(
        (option) =>
          option.repository.name === repoAddress.name &&
          option.repositoryLocation.name === repoAddress.location,
      )
    : null;
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

export const isThisThingAJob = (repo: DagsterRepoOption | null, pipelineOrJobName: string) => {
  const pipelineOrJob = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineOrJobName,
  );
  return !!pipelineOrJob?.isJob;
};

export const buildPipelineSelector = (
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
  } as PipelineSelector;
};

export const optionToRepoAddress = (option: DagsterRepoOption) =>
  buildRepoAddress(option.repository.name, option.repository.location.name);
