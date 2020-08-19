// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionsNameQuery
// ====================================================

export interface PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
}

export interface PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export interface PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause | null;
}

export type PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions | PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError;

export interface PartitionsNameQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitionsOrError: PartitionsNameQuery_partitionSetOrError_PartitionSet_partitionsOrError;
  pipelineName: string;
}

export interface PartitionsNameQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError";
  message: string;
}

export interface PartitionsNameQuery_partitionSetOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type PartitionsNameQuery_partitionSetOrError = PartitionsNameQuery_partitionSetOrError_PartitionSet | PartitionsNameQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionsNameQuery_partitionSetOrError_PythonError;

export interface PartitionsNameQuery {
  partitionSetOrError: PartitionsNameQuery_partitionSetOrError;
}

export interface PartitionsNameQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
}
