/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchBootstrapQuery
// ====================================================

export interface SearchBootstrapQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SearchBootstrapQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SearchBootstrapQuery_workspaceOrError_PythonError_causes[];
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  name: string;
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  name: string;
  pipelineName: string;
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  schedules: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
  sensors: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
  partitionSets: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets[];
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export type SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError | SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation;

export interface SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface SearchBootstrapQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries[];
}

export type SearchBootstrapQuery_workspaceOrError = SearchBootstrapQuery_workspaceOrError_PythonError | SearchBootstrapQuery_workspaceOrError_Workspace;

export interface SearchBootstrapQuery {
  workspaceOrError: SearchBootstrapQuery_workspaceOrError;
}
