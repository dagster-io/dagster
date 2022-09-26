/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus, RunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceOverviewInitialQuery
// ====================================================

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_runs[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  selectorId: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks_results[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  pipelineName: string;
  scheduleState: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState;
  executionTimezone: string | null;
  futureTicks: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks;
  cronSchedule: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets {
  __typename: "Target";
  pipelineName: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  selectorId: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets[] | null;
  sensorState: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState;
  jobOriginId: string;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  location: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location;
  displayMetadata: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata[];
  schedules: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
  sensors: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  locationOrLoadError: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface InstanceOverviewInitialQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceOverviewInitialQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceOverviewInitialQuery_workspaceOrError_PythonError_causes[];
}

export type InstanceOverviewInitialQuery_workspaceOrError = InstanceOverviewInitialQuery_workspaceOrError_Workspace | InstanceOverviewInitialQuery_workspaceOrError_PythonError;

export interface InstanceOverviewInitialQuery {
  workspaceOrError: InstanceOverviewInitialQuery_workspaceOrError;
}
