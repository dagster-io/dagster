/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceJobsQuery
// ====================================================

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  modes: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes[];
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  selectorId: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks_results[];
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  pipelineName: string;
  scheduleState: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState;
  executionTimezone: string | null;
  futureTicks: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks;
  cronSchedule: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets {
  __typename: "Target";
  pipelineName: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  selectorId: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets[] | null;
  sensorState: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState;
  jobOriginId: string;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  location: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location;
  displayMetadata: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata[];
  schedules: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
  sensors: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  locationOrLoadError: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface WorkspaceJobsQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceJobsQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceJobsQuery_workspaceOrError_PythonError_causes[];
}

export type WorkspaceJobsQuery_workspaceOrError = WorkspaceJobsQuery_workspaceOrError_Workspace | WorkspaceJobsQuery_workspaceOrError_PythonError;

export interface WorkspaceJobsQuery {
  workspaceOrError: WorkspaceJobsQuery_workspaceOrError;
}
