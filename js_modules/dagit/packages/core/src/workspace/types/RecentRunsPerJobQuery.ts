/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RecentRunsPerJobQuery
// ====================================================

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_runs[];
}

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
}

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RecentRunsPerJobQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: RecentRunsPerJobQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface RecentRunsPerJobQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RecentRunsPerJobQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RecentRunsPerJobQuery_workspaceOrError_PythonError_causes[];
}

export type RecentRunsPerJobQuery_workspaceOrError = RecentRunsPerJobQuery_workspaceOrError_Workspace | RecentRunsPerJobQuery_workspaceOrError_PythonError;

export interface RecentRunsPerJobQuery {
  workspaceOrError: RecentRunsPerJobQuery_workspaceOrError;
}
