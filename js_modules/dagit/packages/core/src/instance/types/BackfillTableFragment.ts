/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus, BackfillStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: BackfillTableFragment
// ====================================================

export interface BackfillTableFragment_partitionRunStats {
  __typename: "BackfillRunStats";
  numQueued: number;
  numInProgress: number;
  numSucceeded: number;
  numFailed: number;
  numPartitionsWithRuns: number;
  numTotalRuns: number;
}

export interface BackfillTableFragment_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface BackfillTableFragment_runs {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
  status: RunStatus;
  tags: BackfillTableFragment_runs_tags[];
}

export interface BackfillTableFragment_unfinishedRuns {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
}

export interface BackfillTableFragment_partitionSet_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface BackfillTableFragment_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  pipelineName: string;
  repositoryOrigin: BackfillTableFragment_partitionSet_repositoryOrigin;
}

export interface BackfillTableFragment_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface BackfillTableFragment_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: BackfillTableFragment_error_causes[];
}

export interface BackfillTableFragment {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  backfillStatus: BackfillStatus;
  numRequested: number;
  partitionNames: string[];
  numPartitions: number;
  partitionRunStats: BackfillTableFragment_partitionRunStats;
  runs: BackfillTableFragment_runs[];
  unfinishedRuns: BackfillTableFragment_unfinishedRuns[];
  timestamp: number;
  partitionSetName: string;
  partitionSet: BackfillTableFragment_partitionSet | null;
  error: BackfillTableFragment_error | null;
}
