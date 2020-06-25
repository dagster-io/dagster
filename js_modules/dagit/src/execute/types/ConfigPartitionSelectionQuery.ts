// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ConfigPartitionSelectionQuery
// ====================================================

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError_PartitionRunConfig {
  __typename: "PartitionRunConfig";
  yaml: string;
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError_PythonError_cause | null;
}

export type ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError = ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError_PartitionRunConfig | ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError_PythonError;

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PartitionTags_results {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PartitionTags {
  __typename: "PartitionTags";
  results: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PartitionTags_results[];
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PythonError_cause | null;
}

export type ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError = ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PartitionTags | ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError_PythonError;

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition {
  __typename: "Partition";
  name: string;
  solidSelection: string[] | null;
  runConfigOrError: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_runConfigOrError;
  mode: string;
  tagsOrError: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tagsOrError;
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partition: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition | null;
}

export type ConfigPartitionSelectionQuery_partitionSetOrError = ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSetNotFoundError | ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet;

export interface ConfigPartitionSelectionQuery {
  partitionSetOrError: ConfigPartitionSelectionQuery_partitionSetOrError;
}

export interface ConfigPartitionSelectionQueryVariables {
  repositorySelector: RepositorySelector;
  partitionSetName: string;
  partitionName: string;
}
