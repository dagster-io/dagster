// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RootRepositoriesQuery
// ====================================================

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  graphName: string;
  pipelineSnapshotId: string;
  modes: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes[];
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  mode: string;
  pipelineName: string;
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  partitionSets: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets[];
  location: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location;
  displayMetadata: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata[];
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  repositories: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_cause | null;
}

export type RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  updatedTimestamp: number;
  locationOrLoadError: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RootRepositoriesQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: RootRepositoriesQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface RootRepositoriesQuery_workspaceOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootRepositoriesQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootRepositoriesQuery_workspaceOrError_PythonError_cause | null;
}

export type RootRepositoriesQuery_workspaceOrError = RootRepositoriesQuery_workspaceOrError_Workspace | RootRepositoriesQuery_workspaceOrError_PythonError;

export interface RootRepositoriesQuery {
  workspaceOrError: RootRepositoriesQuery_workspaceOrError;
}
