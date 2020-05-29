// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RootRepositoriesQuery
// ====================================================

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_repositories_pipelines {
  __typename: "Pipeline";
  name: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_repositories {
  __typename: "Repository";
  name: string;
  pipelines: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_repositories_pipelines[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes {
  __typename: "RepositoryLocation";
  name: string;
  repositories: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_repositories[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootRepositoriesQuery_repositoryLocationsOrError_PythonError_cause | null;
}

export type RootRepositoriesQuery_repositoryLocationsOrError = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection | RootRepositoriesQuery_repositoryLocationsOrError_PythonError;

export interface RootRepositoriesQuery {
  repositoryLocationsOrError: RootRepositoriesQuery_repositoryLocationsOrError;
}
