/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionProgressQuery
// ====================================================

export interface PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_partitionRunStats {
  __typename: "BackfillRunStats";
  numQueued: number;
  numInProgress: number;
  numSucceeded: number;
  numFailed: number;
  numPartitionsWithRuns: number;
  numTotalRuns: number;
}

export interface PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_unfinishedRuns {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
}

export interface PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  numRequested: number;
  partitionNames: string[];
  numPartitions: number;
  partitionRunStats: PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_partitionRunStats;
  unfinishedRuns: PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_unfinishedRuns[];
}

export interface PartitionProgressQuery_partitionBackfillOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionProgressQuery_partitionBackfillOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionProgressQuery_partitionBackfillOrError_PythonError_cause | null;
}

export type PartitionProgressQuery_partitionBackfillOrError = PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill | PartitionProgressQuery_partitionBackfillOrError_PythonError;

export interface PartitionProgressQuery {
  partitionBackfillOrError: PartitionProgressQuery_partitionBackfillOrError;
}

export interface PartitionProgressQueryVariables {
  backfillId: string;
}
