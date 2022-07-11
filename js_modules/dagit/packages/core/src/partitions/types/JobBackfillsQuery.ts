/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, BulkActionStatus, BackfillStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: JobBackfillsQuery
// ====================================================

export interface JobBackfillsQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionRunStats {
  __typename: "BackfillRunStats";
  numQueued: number;
  numInProgress: number;
  numSucceeded: number;
  numFailed: number;
  numPartitionsWithRuns: number;
  numTotalRuns: number;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_runs {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
  status: RunStatus;
  tags: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_runs_tags[];
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_unfinishedRuns {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionSet_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  pipelineName: string;
  repositoryOrigin: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionSet_repositoryOrigin;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error_causes[];
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  backfillStatus: BackfillStatus;
  numRequested: number;
  partitionNames: string[];
  numPartitions: number;
  partitionRunStats: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionRunStats;
  runs: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_runs[];
  unfinishedRuns: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_unfinishedRuns[];
  timestamp: number;
  partitionSetName: string;
  partitionSet: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionSet | null;
  error: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error | null;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  id: string;
  pipelineName: string;
  backfills: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills[];
}

export type JobBackfillsQuery_partitionSetOrError = JobBackfillsQuery_partitionSetOrError_PartitionSetNotFoundError | JobBackfillsQuery_partitionSetOrError_PartitionSet;

export interface JobBackfillsQuery {
  partitionSetOrError: JobBackfillsQuery_partitionSetOrError;
}

export interface JobBackfillsQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
  cursor?: string | null;
  limit?: number | null;
}
