/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceSchedulesQuery
// ====================================================

export interface WorkspaceSchedulesQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface WorkspaceSchedulesQuery_repositoryOrError_Repository_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  description: string | null;
}

export interface WorkspaceSchedulesQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  schedules: WorkspaceSchedulesQuery_repositoryOrError_Repository_schedules[];
}

export interface WorkspaceSchedulesQuery_repositoryOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceSchedulesQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceSchedulesQuery_repositoryOrError_PythonError_causes[];
}

export type WorkspaceSchedulesQuery_repositoryOrError = WorkspaceSchedulesQuery_repositoryOrError_RepositoryNotFoundError | WorkspaceSchedulesQuery_repositoryOrError_Repository | WorkspaceSchedulesQuery_repositoryOrError_PythonError;

export interface WorkspaceSchedulesQuery {
  repositoryOrError: WorkspaceSchedulesQuery_repositoryOrError;
}

export interface WorkspaceSchedulesQueryVariables {
  selector: RepositorySelector;
}
