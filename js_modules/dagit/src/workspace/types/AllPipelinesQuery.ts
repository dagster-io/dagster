// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AllPipelinesQuery
// ====================================================

export interface AllPipelinesQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
}

export interface AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  name: string;
  runs: AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines_runs[];
  schedules: AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines_schedules[];
  sensors: AllPipelinesQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines_sensors[];
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
