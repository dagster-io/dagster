// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigPartitionsQuery
// ====================================================

export interface ConfigPartitionsQuery_pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPartitionsQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  tags: ConfigPartitionsQuery_pipeline_tags[];
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions {
  __typename: "Partition";
  name: string;
  solidSubset: string[] | null;
  environmentConfigYaml: string;
  mode: string;
  tags: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_tags[];
}

export interface ConfigPartitionsQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitions: ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions[];
}

export type ConfigPartitionsQuery_partitionSetOrError = ConfigPartitionsQuery_partitionSetOrError_PartitionSetNotFoundError | ConfigPartitionsQuery_partitionSetOrError_PartitionSet;

export interface ConfigPartitionsQuery {
  pipeline: ConfigPartitionsQuery_pipeline;
  partitionSetOrError: ConfigPartitionsQuery_partitionSetOrError;
}

export interface ConfigPartitionsQueryVariables {
  partitionSetName: string;
  pipelineName: string;
}
