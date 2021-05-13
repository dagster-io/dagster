// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RepositoryLocationsFragment
// ====================================================

export interface RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  id: string;
  name: string;
  error: RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocationLoading {
  __typename: "RepositoryLocationLoading";
  id: string;
  name: string;
}

export type RepositoryLocationsFragment_RepositoryLocationConnection_nodes = RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocation | RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure | RepositoryLocationsFragment_RepositoryLocationConnection_nodes_RepositoryLocationLoading;

export interface RepositoryLocationsFragment_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: RepositoryLocationsFragment_RepositoryLocationConnection_nodes[];
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

export type RepositoryLocationsFragment = RepositoryLocationsFragment_RepositoryLocationConnection | RepositoryLocationsFragment_PythonError;
