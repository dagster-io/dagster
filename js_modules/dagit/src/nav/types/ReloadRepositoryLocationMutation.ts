// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ReloadRepositoryLocationMutation
// ====================================================

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation_repositories_pipelines[];
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  repositories: ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation_repositories[];
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported {
  __typename: "ReloadNotSupported";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound {
  __typename: "RepositoryLocationNotFound";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  id: string;
  error: ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationLoadFailure_error;
}

export type ReloadRepositoryLocationMutation_reloadRepositoryLocation = ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation | ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported | ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound | ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationLoadFailure;

export interface ReloadRepositoryLocationMutation {
  reloadRepositoryLocation: ReloadRepositoryLocationMutation_reloadRepositoryLocation;
}

export interface ReloadRepositoryLocationMutationVariables {
  location: string;
}
