// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryPipelinesListQuery
// ====================================================

export interface RepositoryPipelinesListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
}

export interface RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  runs: RepositoryPipelinesListQuery_repositoryOrError_Repository_pipelines_runs[];
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
