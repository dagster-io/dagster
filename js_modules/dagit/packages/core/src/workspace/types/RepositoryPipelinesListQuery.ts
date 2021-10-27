// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryPipelinesListQuery
// ====================================================

export interface RepositoryPipelinesListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_runs {
  __typename: "Run";
  id: string;
  mode: string;
  runId: string;
  status: RunStatus;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  mode: string;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_sensors_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_sensors_targets[] | null;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  isJob: boolean;
  name: string;
  modes: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_modes[];
  runs: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_runs[];
  schedules: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_schedules[];
  sensors: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_sensors[];
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  pipelines: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines[];
}

export interface RepositoryPipelinesListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositoryPipelinesListQuery_repositoryOrError = RepositoryPipelinesListQuery_repositoryOrError_PythonError | RepositoryPipelinesListQuery_repositoryOrError_Repository | RepositoryPipelinesListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositoryPipelinesListQuery {
  repositoryOrError: RepositoryPipelinesListQuery_repositoryOrError;
}

export interface RepositoryPipelinesListQueryVariables {
  repositorySelector: RepositorySelector;
}
