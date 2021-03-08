// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ReloadWorkspaceMutation
// ====================================================

export interface ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocation_repositories_pipelines[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  repositories: ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocation_repositories[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error {
  __typename: "PythonError";
  message: string;
}

export interface ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure {
  __typename: "RepositoryLocationLoadFailure";
  id: string;
  error: ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure_error;
}

export type ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes = ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocation | ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes_RepositoryLocationLoadFailure;

export interface ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection {
  __typename: "RepositoryLocationConnection";
  nodes: ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection_nodes[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ReloadWorkspaceMutation_reloadWorkspace_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ReloadWorkspaceMutation_reloadWorkspace_PythonError_cause | null;
}

export type ReloadWorkspaceMutation_reloadWorkspace = ReloadWorkspaceMutation_reloadWorkspace_RepositoryLocationConnection | ReloadWorkspaceMutation_reloadWorkspace_PythonError;

export interface ReloadWorkspaceMutation {
  reloadWorkspace: ReloadWorkspaceMutation_reloadWorkspace;
}
