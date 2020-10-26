// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ReloadRepositoryLocationMutation
// ====================================================

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation {
  __typename: "RepositoryLocation";
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported {
  __typename: "ReloadNotSupported";
  message: string;
}

export interface ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound {
  __typename: "RepositoryLocationNotFound";
  message: string;
}

export type ReloadRepositoryLocationMutation_reloadRepositoryLocation = ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocation | ReloadRepositoryLocationMutation_reloadRepositoryLocation_ReloadNotSupported | ReloadRepositoryLocationMutation_reloadRepositoryLocation_RepositoryLocationNotFound;

export interface ReloadRepositoryLocationMutation {
  reloadRepositoryLocation: ReloadRepositoryLocationMutation_reloadRepositoryLocation;
}

export interface ReloadRepositoryLocationMutationVariables {
  location: string;
}
