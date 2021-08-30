// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ReloadRepositoryLocationMutation
// ====================================================

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  repositories: ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_PythonError_cause | null;
}

export type ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError = ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_RepositoryLocation | ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError_PythonError;

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError: ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry_locationOrLoadError | null;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_UnauthorizedError {
  __typename: "UnauthorizedError";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported {
  __typename: "ReloadNotSupported";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound {
  __typename: "RepositoryLocationNotFound";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_PythonError {
  __typename: "PythonError";
  message: string;
}

export type ReloadRepositoryLocationMutation_reloadRepositoryLocation = ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry | ReloadRepositoryLocationMutation_reloadRepositoryLocation_UnauthorizedError | ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported | ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound | ReloadRepositoryLocationMutation_reloadRepositoryLocation_PythonError;

export interface ReloadRepositoryLocationMutation {
  reloadRepositoryLocation: ReloadRepositoryLocationMutation_reloadRepositoryLocation;
}

export interface ReloadRepositoryLocationMutationVariables {
  location: string;
}
