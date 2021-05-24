// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RepositoryLocationsFragment
// ====================================================

export interface RepositoryLocationsFragment_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositoryLocationsFragment_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
}

export interface RepositoryLocationsFragment_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type RepositoryLocationsFragment_Workspace_locationEntries_locationOrLoadError = RepositoryLocationsFragment_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | RepositoryLocationsFragment_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface RepositoryLocationsFragment_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: RepositoryLocationsFragment_Workspace_locationEntries_displayMetadata[];
  updatedTimestamp: number;
  locationOrLoadError: RepositoryLocationsFragment_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RepositoryLocationsFragment_Workspace {
  __typename: "Workspace";
  locationEntries: RepositoryLocationsFragment_Workspace_locationEntries[];
}

export interface RepositoryLocationsFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RepositoryLocationsFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RepositoryLocationsFragment_PythonError_cause | null;
}

export type RepositoryLocationsFragment = RepositoryLocationsFragment_Workspace | RepositoryLocationsFragment_PythonError;
