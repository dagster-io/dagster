// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RootRepositoriesQuery
// ====================================================

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  name: string;
  pipelineSnapshotId: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  pipelineName: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_PythonRepositoryOrigin | RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin_GrpcRepositoryOrigin;

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  name: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines[];
  partitionSets: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_partitionSets[];
  origin: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_origin;
  location: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_location;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  isReloadSupported: boolean;
  name: string;
  repositories: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  name: string;
  error: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
}

export type RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation | RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure;

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
