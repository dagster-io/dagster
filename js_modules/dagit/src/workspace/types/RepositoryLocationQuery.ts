// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RepositoryLocationQuery
// ====================================================

export interface RepositoryLocationQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  name: string;
}

export interface RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  name: string;
  error: RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
}

export type RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation | RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure;

export interface RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes[];
}

export type RepositoryLocationQuery_repositoryLocationsOrError = RepositoryLocationQuery_repositoryLocationsOrError_PythonError | RepositoryLocationQuery_repositoryLocationsOrError_RepositoryLocationConnection;

export interface RepositoryLocationQuery {
  repositoryLocationsOrError: RepositoryLocationQuery_repositoryLocationsOrError;
}
