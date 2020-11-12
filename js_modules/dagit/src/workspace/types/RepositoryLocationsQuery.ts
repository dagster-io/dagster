// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RepositoryLocationsQuery
// ====================================================

export interface RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
}

export interface RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  id: string;
  name: string;
  error: RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
}

export type RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation | RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure;

export interface RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes[];
}

export interface RepositoryLocationsQuery_repositoryLocationsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RepositoryLocationsQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RepositoryLocationsQuery_repositoryLocationsOrError_PythonError_cause | null;
}

export type RepositoryLocationsQuery_repositoryLocationsOrError = RepositoryLocationsQuery_repositoryLocationsOrError_RepositoryLocationConnection | RepositoryLocationsQuery_repositoryLocationsOrError_PythonError;

export interface RepositoryLocationsQuery {
  repositoryLocationsOrError: RepositoryLocationsQuery_repositoryLocationsOrError;
}
