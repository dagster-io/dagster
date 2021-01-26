// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SnapshotQuery
// ====================================================

export interface SnapshotQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PipelineSnapshotNotFoundError" | "PythonError";
}

export interface SnapshotQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  parentSnapshotId: string | null;
}

export type SnapshotQuery_pipelineSnapshotOrError = SnapshotQuery_pipelineSnapshotOrError_PipelineNotFoundError | SnapshotQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface SnapshotQuery {
  pipelineSnapshotOrError: SnapshotQuery_pipelineSnapshotOrError;
}

export interface SnapshotQueryVariables {
  snapshotId: string;
}
