// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AllPipelinesQuery
// ====================================================

export interface AllPipelinesQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines[];
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories[];
}

export type AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure | AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation;

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes[];
}

export type AllPipelinesQuery_repositoryLocationsOrError = AllPipelinesQuery_repositoryLocationsOrError_PythonError | AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection;

export interface AllPipelinesQuery {
  repositoryLocationsOrError: AllPipelinesQuery_repositoryLocationsOrError;
}
