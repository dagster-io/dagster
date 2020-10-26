// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RootRepositoriesQuery
// ====================================================

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_pipelines {
  __typename: "Pipeline";
  name: string;
  pipelineSnapshotId: string;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_partitionSets {
  __typename: "PartitionSet";
  pipelineName: string;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  name: string;
  isReloadSupported: boolean;
  environmentPath: string | null;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin = RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_PythonRepositoryOrigin | RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin_GrpcRepositoryOrigin;

export interface RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_pipelines[];
  partitionSets: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_partitionSets[];
  location: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  origin: RootRepositoriesQuery_repositoriesOrError_RepositoryConnection_nodes_origin;
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
