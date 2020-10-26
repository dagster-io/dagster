// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ConfigPartitionsQuery
// ====================================================

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause | null;
}

export type ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions | ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError;

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitionsOrError: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitionsOrError;
}

export type ConfigPartitionsQuery_partitionSetOrError = ConfigPartitionsQuery_partitionSetOrError_PartitionSetNotFoundError | ConfigPartitionsQuery_partitionSetOrError_PartitionSet;

export interface ConfigPartitionsQuery {
  partitionSetOrError: ConfigPartitionsQuery_partitionSetOrError;
}

export interface ConfigPartitionsQueryVariables {
  repositorySelector: RepositorySelector;
  partitionSetName: string;
}
