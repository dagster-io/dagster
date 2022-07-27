/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ReloadRepositoryLocationMutation
// ====================================================

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry {
  __typename: "WorkspaceLocationEntry";
  id: string;
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

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: ReloadRepositoryLocationMutation_reloadRepositoryLocation_PythonError_causes[];
}

export type ReloadRepositoryLocationMutation_reloadRepositoryLocation = ReloadRepositoryLocationMutation_reloadRepositoryLocation_WorkspaceLocationEntry | ReloadRepositoryLocationMutation_reloadRepositoryLocation_UnauthorizedError | ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported | ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound | ReloadRepositoryLocationMutation_reloadRepositoryLocation_PythonError;

export interface ReloadRepositoryLocationMutation {
  reloadRepositoryLocation: ReloadRepositoryLocationMutation_reloadRepositoryLocation;
}

export interface ReloadRepositoryLocationMutationVariables {
  location: string;
}
