/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CodeLocationStatusQuery
// ====================================================

export interface CodeLocationStatusQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
}

export interface CodeLocationStatusQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface CodeLocationStatusQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: CodeLocationStatusQuery_workspaceOrError_Workspace_locationEntries[];
}

export type CodeLocationStatusQuery_workspaceOrError = CodeLocationStatusQuery_workspaceOrError_PythonError | CodeLocationStatusQuery_workspaceOrError_Workspace;

export interface CodeLocationStatusQuery {
  workspaceOrError: CodeLocationStatusQuery_workspaceOrError;
}
