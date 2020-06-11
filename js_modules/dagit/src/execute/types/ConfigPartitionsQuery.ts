// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ConfigPartitionsQuery
// ====================================================

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results {
  __typename: "Partition";
  name: string;
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions {
  __typename: "Partitions";
  results: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results[];
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitions: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions;
}

export type ConfigPartitionsQuery_partitionSetOrError = ConfigPartitionsQuery_partitionSetOrError_PartitionSetNotFoundError | ConfigPartitionsQuery_partitionSetOrError_PartitionSet;

export interface ConfigPartitionsQuery {
  partitionSetOrError: ConfigPartitionsQuery_partitionSetOrError;
}

export interface ConfigPartitionsQueryVariables {
  repositorySelector: RepositorySelector;
  partitionSetName: string;
}
