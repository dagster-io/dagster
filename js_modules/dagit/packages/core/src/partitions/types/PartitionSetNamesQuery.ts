/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionSetNamesQuery
// ====================================================

export interface PartitionSetNamesQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
}

export interface PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export interface PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause | null;
}

export type PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions | PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError;

export interface PartitionSetNamesQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionsOrError: PartitionSetNamesQuery_partitionSetOrError_PartitionSet_partitionsOrError;
}

export type PartitionSetNamesQuery_partitionSetOrError = PartitionSetNamesQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionSetNamesQuery_partitionSetOrError_PartitionSet;

export interface PartitionSetNamesQuery {
  partitionSetOrError: PartitionSetNamesQuery_partitionSetOrError;
}

export interface PartitionSetNamesQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
  limit?: number | null;
  cursor?: string | null;
  reverse?: boolean | null;
}
