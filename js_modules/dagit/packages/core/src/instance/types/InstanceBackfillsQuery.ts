/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus, BackfillStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceBackfillsQuery
// ====================================================

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

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runId: string | null;
  runStatus: RunStatus | null;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionStatuses {
  __typename: "PartitionStatuses";
  results: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionStatuses_results[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  backfillStatus: BackfillStatus;
  numRequested: number;
  numPartitions: number;
  timestamp: number;
  partitionSetName: string;
  partitionSet: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet | null;
  error: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error | null;
  partitionNames: string[];
  partitionStatuses: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionStatuses;
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
