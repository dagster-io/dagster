/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryLocationStatusQuery
// ====================================================

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
}

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  repositories: RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError: RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RepositoryLocationStatusQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: RepositoryLocationStatusQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface RepositoryLocationStatusQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RepositoryLocationStatusQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RepositoryLocationStatusQuery_workspaceOrError_PythonError_causes[];
}

export type RepositoryLocationStatusQuery_workspaceOrError = RepositoryLocationStatusQuery_workspaceOrError_Workspace | RepositoryLocationStatusQuery_workspaceOrError_PythonError;

export interface RepositoryLocationStatusQuery {
  workspaceOrError: RepositoryLocationStatusQuery_workspaceOrError;
}
