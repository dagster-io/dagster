/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OverviewSchedulesQuery
// ====================================================

export interface OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  description: string | null;
}

export interface OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  schedules: OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
}

export interface OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface OverviewSchedulesQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: OverviewSchedulesQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface OverviewSchedulesQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewSchedulesQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewSchedulesQuery_workspaceOrError_PythonError_causes[];
}

export type OverviewSchedulesQuery_workspaceOrError = OverviewSchedulesQuery_workspaceOrError_Workspace | OverviewSchedulesQuery_workspaceOrError_PythonError;

export interface OverviewSchedulesQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
}

export interface OverviewSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
}

export interface OverviewSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: OverviewSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export type OverviewSchedulesQuery_unloadableInstigationStatesOrError = OverviewSchedulesQuery_unloadableInstigationStatesOrError_PythonError | OverviewSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates;

export interface OverviewSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes[];
}

export interface OverviewSchedulesQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: OverviewSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface OverviewSchedulesQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: OverviewSchedulesQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface OverviewSchedulesQuery_instance {
  __typename: "Instance";
  daemonHealth: OverviewSchedulesQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface OverviewSchedulesQuery {
  workspaceOrError: OverviewSchedulesQuery_workspaceOrError;
  unloadableInstigationStatesOrError: OverviewSchedulesQuery_unloadableInstigationStatesOrError;
  instance: OverviewSchedulesQuery_instance;
}
