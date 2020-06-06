// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigPartitionSetsQuery
// ====================================================

export interface ConfigPartitionSetsQuery_partitionSetsOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PythonError";
}

export interface ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results {
  __typename: "PartitionSet";
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets {
  __typename: "PartitionSets";
  results: ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results[];
}

export type ConfigPartitionSetsQuery_partitionSetsOrError = ConfigPartitionSetsQuery_partitionSetsOrError_PipelineNotFoundError | ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets;

export interface ConfigPartitionSetsQuery {
  partitionSetsOrError: ConfigPartitionSetsQuery_partitionSetsOrError;
}

export interface ConfigPartitionSetsQueryVariables {
  pipelineName: string;
}
