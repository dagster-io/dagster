/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, BulkActionStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: JobBackfillsQuery
// ====================================================

export interface JobBackfillsQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
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

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error_errorChain_error;
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_error_errorChain[];
}

export interface JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  numCancelable: number;
  partitionNames: string[];
  numPartitions: number;
  timestamp: number;
  partitionSetName: string;
  partitionSet: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_partitionSet | null;
  assetSelection: JobBackfillsQuery_partitionSetOrError_PartitionSet_backfills_assetSelection[] | null;
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
