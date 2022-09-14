/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: WorkspaceJobsQuery
// ====================================================

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
}

export interface WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: WorkspaceJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
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
