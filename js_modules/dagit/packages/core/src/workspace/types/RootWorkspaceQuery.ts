/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RootWorkspaceQuery
// ====================================================

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  graphName: string;
  pipelineSnapshotId: string;
  modes: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  cronSchedule: string;
  executionTimezone: string | null;
  mode: string;
  name: string;
  pipelineName: string;
  scheduleState: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  targets: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets[] | null;
  sensorState: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  mode: string;
  pipelineName: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_assetGroups {
  __typename: "AssetGroup";
  groupName: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  schedules: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
  sensors: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
  partitionSets: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets[];
  assetGroups: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_assetGroups[];
  location: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location;
  displayMetadata: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  repositories: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  updatedTimestamp: number;
  locationOrLoadError: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface RootWorkspaceQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RootWorkspaceQuery_workspaceOrError_PythonError_causes[];
}

export type RootWorkspaceQuery_workspaceOrError = RootWorkspaceQuery_workspaceOrError_Workspace | RootWorkspaceQuery_workspaceOrError_PythonError;

export interface RootWorkspaceQuery {
  workspaceOrError: RootWorkspaceQuery_workspaceOrError;
}
