/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceSensorsQuery
// ====================================================

export interface WorkspaceSensorsQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface WorkspaceSensorsQuery_repositoryOrError_Repository_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  description: string | null;
}

export interface WorkspaceSensorsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  sensors: WorkspaceSensorsQuery_repositoryOrError_Repository_sensors[];
}

export interface WorkspaceSensorsQuery_repositoryOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceSensorsQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceSensorsQuery_repositoryOrError_PythonError_causes[];
}

export type WorkspaceSensorsQuery_repositoryOrError = WorkspaceSensorsQuery_repositoryOrError_RepositoryNotFoundError | WorkspaceSensorsQuery_repositoryOrError_Repository | WorkspaceSensorsQuery_repositoryOrError_PythonError;

export interface WorkspaceSensorsQuery {
  repositoryOrError: WorkspaceSensorsQuery_repositoryOrError;
}

export interface WorkspaceSensorsQueryVariables {
  selector: RepositorySelector;
}
