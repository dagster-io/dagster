/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ReloadWorkspaceMutation
// ====================================================

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  repositories: ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError = ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  name: string;
  id: string;
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError: ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries_locationOrLoadError | null;
}

export interface ReloadWorkspaceMutation_reloadWorkspace_Workspace {
  __typename: "Workspace";
  locationEntries: ReloadWorkspaceMutation_reloadWorkspace_Workspace_locationEntries[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_UnauthorizedError {
  __typename: "UnauthorizedError";
  message: string;
}

export interface ReloadWorkspaceMutation_reloadWorkspace_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: ReloadWorkspaceMutation_reloadWorkspace_PythonError_causes[];
}

export type ReloadWorkspaceMutation_reloadWorkspace = ReloadWorkspaceMutation_reloadWorkspace_Workspace | ReloadWorkspaceMutation_reloadWorkspace_UnauthorizedError | ReloadWorkspaceMutation_reloadWorkspace_PythonError;

export interface ReloadWorkspaceMutation {
  reloadWorkspace: ReloadWorkspaceMutation_reloadWorkspace;
}
