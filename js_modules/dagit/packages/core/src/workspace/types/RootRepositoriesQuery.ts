// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RootRepositoriesQuery
// ====================================================

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  pipelineSnapshotId: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  pipelineName: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines[];
  partitionSets: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_partitionSets[];
  location: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_location;
  displayMetadata: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_displayMetadata[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  loadStatus: RepositoryLocationLoadStatus;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  repositories: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error_cause | null;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  error: RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
}

export interface RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoading {
  __typename: "RepositoryLocationLoading";
  id: string;
  name: string;
}

export type RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation | RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure | RootRepositoriesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoading;

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
