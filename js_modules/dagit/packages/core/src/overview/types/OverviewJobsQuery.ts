/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OverviewJobsQuery
// ====================================================

export interface OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
}

export interface OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
}

export interface OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface OverviewJobsQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: OverviewJobsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface OverviewJobsQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: OverviewJobsQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface OverviewJobsQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewJobsQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewJobsQuery_workspaceOrError_PythonError_causes[];
}

export type OverviewJobsQuery_workspaceOrError = OverviewJobsQuery_workspaceOrError_Workspace | OverviewJobsQuery_workspaceOrError_PythonError;

export interface OverviewJobsQuery {
  workspaceOrError: OverviewJobsQuery_workspaceOrError;
}
