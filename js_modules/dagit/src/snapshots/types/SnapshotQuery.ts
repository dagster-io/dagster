// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SnapshotQuery
// ====================================================

export interface SnapshotQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError" | "PipelineNotFoundError" | "PythonError";
}

export interface SnapshotQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  parentSnapshotId: string | null;
}

export type SnapshotQuery_pipelineSnapshotOrError = SnapshotQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | SnapshotQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface SnapshotQuery {
  pipelineSnapshotOrError: SnapshotQuery_pipelineSnapshotOrError;
}

export interface SnapshotQueryVariables {
  snapshotId: string;
}
