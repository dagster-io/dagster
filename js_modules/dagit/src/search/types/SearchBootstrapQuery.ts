// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchBootstrapQuery
// ====================================================

export interface SearchBootstrapQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines[];
  schedules: SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_schedules[];
  sensors: SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_sensors[];
  partitionSets: SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_partitionSets[];
}

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories[];
}

export type SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure | SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation;

export interface SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes[];
}

export type SearchBootstrapQuery_repositoryLocationsOrError = SearchBootstrapQuery_repositoryLocationsOrError_PythonError | SearchBootstrapQuery_repositoryLocationsOrError_RepositoryLocationConnection;

export interface SearchBootstrapQuery {
  repositoryLocationsOrError: SearchBootstrapQuery_repositoryLocationsOrError;
}
