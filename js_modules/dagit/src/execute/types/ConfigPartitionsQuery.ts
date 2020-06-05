// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ConfigPartitionsQuery
// ====================================================

export interface ConfigPartitionsQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface ConfigPartitionsQuery_pipelineOrError_Pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPartitionsQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  tags: ConfigPartitionsQuery_pipelineOrError_Pipeline_tags[];
}

export type ConfigPartitionsQuery_pipelineOrError = ConfigPartitionsQuery_pipelineOrError_PipelineNotFoundError | ConfigPartitionsQuery_pipelineOrError_Pipeline;

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
  pipelineOrError: ConfigPartitionsQuery_pipelineOrError;
  partitionSetOrError: ConfigPartitionsQuery_partitionSetOrError;
}

export interface ConfigPartitionsQueryVariables {
  repositorySelector: RepositorySelector;
  pipelineSelector: PipelineSelector;
  partitionSetName: string;
}
