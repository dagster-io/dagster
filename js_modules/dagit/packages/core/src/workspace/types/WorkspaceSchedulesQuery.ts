/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: WorkspaceSchedulesQuery
// ====================================================

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  description: string | null;
}

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  schedules: WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
}

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface WorkspaceSchedulesQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: WorkspaceSchedulesQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface WorkspaceSchedulesQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceSchedulesQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceSchedulesQuery_workspaceOrError_PythonError_causes[];
}

export type WorkspaceSchedulesQuery_workspaceOrError = WorkspaceSchedulesQuery_workspaceOrError_Workspace | WorkspaceSchedulesQuery_workspaceOrError_PythonError;

export interface WorkspaceSchedulesQuery {
  workspaceOrError: WorkspaceSchedulesQuery_workspaceOrError;
}
