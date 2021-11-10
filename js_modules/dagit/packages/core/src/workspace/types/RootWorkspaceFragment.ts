// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RootWorkspaceFragment
// ====================================================

export interface RootWorkspaceFragment_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  scheduleState: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules_scheduleState;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors_targets[] | null;
  sensorState: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors_sensorState;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  graphName: string;
  pipelineSnapshotId: string;
  modes: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes[];
  schedules: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_schedules[];
  sensors: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_sensors[];
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  mode: string;
  pipelineName: string;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  partitionSets: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets[];
  location: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location;
  displayMetadata: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata[];
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  repositories: RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootWorkspaceFragment_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootWorkspaceFragment_locationEntries_locationOrLoadError_PythonError_cause | null;
}

export type RootWorkspaceFragment_locationEntries_locationOrLoadError = RootWorkspaceFragment_locationEntries_locationOrLoadError_RepositoryLocation | RootWorkspaceFragment_locationEntries_locationOrLoadError_PythonError;

export interface RootWorkspaceFragment_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: RootWorkspaceFragment_locationEntries_displayMetadata[];
  updatedTimestamp: number;
  locationOrLoadError: RootWorkspaceFragment_locationEntries_locationOrLoadError | null;
}

export interface RootWorkspaceFragment {
  __typename: "Workspace";
  locationEntries: RootWorkspaceFragment_locationEntries[];
}
