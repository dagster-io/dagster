/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RunningBackfillsNoticeQuery
// ====================================================

export interface RunningBackfillsNoticeQuery_partitionBackfillsOrError_PythonError {
  __typename: "PythonError";
}

export interface RunningBackfillsNoticeQuery_partitionBackfillsOrError_PartitionBackfills_results {
  __typename: "PartitionBackfill";
  partitionSetName: string;
  backfillId: string;
}

export interface RunningBackfillsNoticeQuery_partitionBackfillsOrError_PartitionBackfills {
  __typename: "PartitionBackfills";
  results: RunningBackfillsNoticeQuery_partitionBackfillsOrError_PartitionBackfills_results[];
}

export type RunningBackfillsNoticeQuery_partitionBackfillsOrError = RunningBackfillsNoticeQuery_partitionBackfillsOrError_PythonError | RunningBackfillsNoticeQuery_partitionBackfillsOrError_PartitionBackfills;

export interface RunningBackfillsNoticeQuery {
  partitionBackfillsOrError: RunningBackfillsNoticeQuery_partitionBackfillsOrError;
}
