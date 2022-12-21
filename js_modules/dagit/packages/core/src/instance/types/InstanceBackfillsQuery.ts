/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus } from "./../../types/globalTypes";

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

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error_errorChain_error;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error_errorChain[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  numRequested: number;
  numPartitions: number;
  timestamp: number;
  partitionSetName: string;
  partitionSet: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet | null;
  error: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_error | null;
  partitionNames: string[];
  assetSelection: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_assetSelection[] | null;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills {
  __typename: "PartitionBackfills";
  results: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PythonError_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PythonError_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: InstanceBackfillsQuery_partitionBackfillsOrError_PythonError_errorChain_error;
}

export interface InstanceBackfillsQuery_partitionBackfillsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: InstanceBackfillsQuery_partitionBackfillsOrError_PythonError_errorChain[];
}

export type InstanceBackfillsQuery_partitionBackfillsOrError = InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills | InstanceBackfillsQuery_partitionBackfillsOrError_PythonError;

export interface InstanceBackfillsQuery {
  partitionBackfillsOrError: InstanceBackfillsQuery_partitionBackfillsOrError;
}

export interface InstanceBackfillsQueryVariables {
  cursor?: string | null;
  limit?: number | null;
}
