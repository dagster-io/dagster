/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceJobsQuery
// ====================================================

export interface WorkspaceJobsQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface WorkspaceJobsQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
}

export interface WorkspaceJobsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: WorkspaceJobsQuery_repositoryOrError_Repository_pipelines[];
}

export interface WorkspaceJobsQuery_repositoryOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceJobsQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceJobsQuery_repositoryOrError_PythonError_causes[];
}

export type WorkspaceJobsQuery_repositoryOrError = WorkspaceJobsQuery_repositoryOrError_RepositoryNotFoundError | WorkspaceJobsQuery_repositoryOrError_Repository | WorkspaceJobsQuery_repositoryOrError_PythonError;

export interface WorkspaceJobsQuery {
  repositoryOrError: WorkspaceJobsQuery_repositoryOrError;
}

export interface WorkspaceJobsQueryVariables {
  selector: RepositorySelector;
}
