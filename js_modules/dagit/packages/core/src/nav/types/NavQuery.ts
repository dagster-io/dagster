// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: NavQuery
// ====================================================

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  scheduleState: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules_scheduleState;
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors {
  __typename: "Sensor";
  id: string;
  mode: string | null;
  name: string;
  sensorState: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors_sensorState;
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  modes: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes[];
  schedules: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules[];
  sensors: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors[];
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_assetDefinitions_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_assetDefinitions {
  __typename: "AssetDefinition";
  id: string;
  assetKey: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_assetDefinitions_assetKey;
  jobName: string | null;
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  assetDefinitions: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_assetDefinitions[];
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_cause | null;
}

export type NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface NavQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: NavQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface NavQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: NavQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface NavQuery_workspaceOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface NavQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: NavQuery_workspaceOrError_PythonError_cause | null;
}

export type NavQuery_workspaceOrError = NavQuery_workspaceOrError_Workspace | NavQuery_workspaceOrError_PythonError;

export interface NavQuery {
  workspaceOrError: NavQuery_workspaceOrError;
}
