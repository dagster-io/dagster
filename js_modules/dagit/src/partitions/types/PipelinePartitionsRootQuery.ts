// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelinePartitionsRootQuery
// ====================================================

export interface PipelinePartitionsRootQuery_partitionSetsOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PipelinePartitionsRootQuery_partitionSetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export interface PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results {
  __typename: "PartitionSet";
  name: string;
}

export interface PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets {
  __typename: "PartitionSets";
  results: PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results[];
}

export type PipelinePartitionsRootQuery_partitionSetsOrError = PipelinePartitionsRootQuery_partitionSetsOrError_PipelineNotFoundError | PipelinePartitionsRootQuery_partitionSetsOrError_PythonError | PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets;

export interface PipelinePartitionsRootQuery {
  partitionSetsOrError: PipelinePartitionsRootQuery_partitionSetsOrError;
}

export interface PipelinePartitionsRootQueryVariables {
  pipelineName: string;
  repositorySelector: RepositorySelector;
}
