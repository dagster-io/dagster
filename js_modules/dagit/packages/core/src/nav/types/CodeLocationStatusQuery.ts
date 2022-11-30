/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CodeLocationStatusQuery
// ====================================================

export interface CodeLocationStatusQuery_locationStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface CodeLocationStatusQuery_locationStatusesOrError_WorkspaceLocationStatusEntries_entries {
  __typename: "WorkspaceLocationStatusEntry";
  id: string;
  loadStatus: RepositoryLocationLoadStatus;
}

export interface CodeLocationStatusQuery_locationStatusesOrError_WorkspaceLocationStatusEntries {
  __typename: "WorkspaceLocationStatusEntries";
  entries: CodeLocationStatusQuery_locationStatusesOrError_WorkspaceLocationStatusEntries_entries[];
}

export type CodeLocationStatusQuery_locationStatusesOrError = CodeLocationStatusQuery_locationStatusesOrError_PythonError | CodeLocationStatusQuery_locationStatusesOrError_WorkspaceLocationStatusEntries;

export interface CodeLocationStatusQuery {
  locationStatusesOrError: CodeLocationStatusQuery_locationStatusesOrError;
}
