// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceHealthQuery
// ====================================================

export interface InstanceHealthQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceHealthQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceHealthQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface InstanceHealthQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceHealthQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceHealthQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceHealthQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceHealthQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceHealthQuery_instance_daemonHealth;
}

export interface InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  id: string;
  name: string;
  error: InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoading {
  __typename: "RepositoryLocationLoading";
  id: string;
  name: string;
}

export type InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes = InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocation | InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure | InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes_RepositoryLocationLoading;

export interface InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection_nodes[];
}

export interface InstanceHealthQuery_repositoryLocationsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceHealthQuery_repositoryLocationsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceHealthQuery_repositoryLocationsOrError_PythonError_cause | null;
}

export type InstanceHealthQuery_repositoryLocationsOrError = InstanceHealthQuery_repositoryLocationsOrError_RepositoryLocationConnection | InstanceHealthQuery_repositoryLocationsOrError_PythonError;

export interface InstanceHealthQuery {
  instance: InstanceHealthQuery_instance;
  repositoryLocationsOrError: InstanceHealthQuery_repositoryLocationsOrError;
}
