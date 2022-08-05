/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceUpdateCheckQuery
// ====================================================

export interface WorkspaceUpdateCheckQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
}

export interface WorkspaceUpdateCheckQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface WorkspaceUpdateCheckQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: WorkspaceUpdateCheckQuery_workspaceOrError_Workspace_locationEntries[];
}

export type WorkspaceUpdateCheckQuery_workspaceOrError = WorkspaceUpdateCheckQuery_workspaceOrError_PythonError | WorkspaceUpdateCheckQuery_workspaceOrError_Workspace;

export interface WorkspaceUpdateCheckQuery {
  workspaceOrError: WorkspaceUpdateCheckQuery_workspaceOrError;
}
