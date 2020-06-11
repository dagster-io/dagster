// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RootRepositoriesQuery
// ====================================================

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_pipelines {
  __typename: "Pipeline";
  name: string;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  name: string;
  environmentPath: string | null;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  name: string;
  pipelines: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_pipelines[];
  location: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface RootRepositoriesQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootRepositoriesQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootRepositoriesQuery_repositoriesOrError_PythonError_cause | null;
}

export type RootRepositoriesQuery_repositoriesOrError = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection | RootRepositoriesQuery_repositoriesOrError_PythonError;

export interface RootRepositoriesQuery {
  repositoriesOrError: RootRepositoriesQuery_repositoriesOrError;
}
