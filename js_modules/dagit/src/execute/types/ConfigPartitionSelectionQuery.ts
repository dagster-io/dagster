// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigPartitionSelectionQuery
// ====================================================

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition {
  __typename: "Partition";
  name: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  mode: string;
  tags: ConfigPartitionSelectionQuery_partitionSetOrError_PartitionSet_partition_tags[];
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
  partitionSetName: string;
  partitionName: string;
}
