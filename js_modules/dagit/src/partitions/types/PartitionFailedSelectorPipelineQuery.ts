// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionFailedSelectorPipelineQuery
// ====================================================

export interface PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
}

export interface PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
}

export interface PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
  runs: PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs[];
}

export interface PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export type PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError | PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions;

export interface PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitionsOrError: PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError;
}

export type PartitionFailedSelectorPipelineQuery_partitionSetOrError = PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionFailedSelectorPipelineQuery_partitionSetOrError_PartitionSet;

export interface PartitionFailedSelectorPipelineQuery {
  partitionSetOrError: PartitionFailedSelectorPipelineQuery_partitionSetOrError;
}

export interface PartitionFailedSelectorPipelineQueryVariables {
  repositorySelector: RepositorySelector;
  partitionSetName: string;
}
