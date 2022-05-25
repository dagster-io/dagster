/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus, BackfillStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceBackfillsQuery
// ====================================================

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionRunStats {
  __typename: "BackfillRunStats";
  numQueued: number;
  numInProgress: number;
  numSucceeded: number;
  numFailed: number;
  numPartitionsWithRuns: number;
  numTotalRuns: number;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_unfinishedRuns {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  pipelineName: string;
  repositoryOrigin: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet_repositoryOrigin;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error_cause | null;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  backfillStatus: BackfillStatus;
  numRequested: number;
  numPartitions: number;
  partitionRunStats: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionRunStats;
  unfinishedRuns: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_unfinishedRuns[];
  timestamp: number;
  partitionSetName: string;
  partitionSet: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet | null;
  error: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error | null;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills {
  __typename: "PartitionBackfills";
  results: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceBackfillsQuery_partitionBackfillsOrError_PythonError_cause | null;
}

export type InstanceBackfillsQuery_partitionBackfillsOrError = InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills | InstanceBackfillsQuery_partitionBackfillsOrError_PythonError;

export interface InstanceBackfillsQuery {
  partitionBackfillsOrError: InstanceBackfillsQuery_partitionBackfillsOrError;
}

export interface InstanceBackfillsQueryVariables {
  cursor?: string | null;
  limit?: number | null;
}
