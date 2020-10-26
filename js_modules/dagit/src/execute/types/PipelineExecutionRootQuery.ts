// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExecutionRootQuery
// ====================================================

export interface PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError {
  __typename: "InvalidSubsetError";
}

export interface PipelineExecutionRootQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_presets_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: PipelineExecutionRootQuery_pipelineOrError_Pipeline_presets_tags[];
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  presets: PipelineExecutionRootQuery_pipelineOrError_Pipeline_presets[];
  tags: PipelineExecutionRootQuery_pipelineOrError_Pipeline_tags[];
  modes: PipelineExecutionRootQuery_pipelineOrError_Pipeline_modes[];
}

export type PipelineExecutionRootQuery_pipelineOrError = PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError | PipelineExecutionRootQuery_pipelineOrError_PipelineNotFoundError | PipelineExecutionRootQuery_pipelineOrError_PythonError | PipelineExecutionRootQuery_pipelineOrError_Pipeline;

export interface PipelineExecutionRootQuery_partitionSetsOrError_PartitionSets_results {
  __typename: "PartitionSet";
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface PipelineExecutionRootQuery_partitionSetsOrError_PartitionSets {
  __typename: "PartitionSets";
  results: PipelineExecutionRootQuery_partitionSetsOrError_PartitionSets_results[];
}

export interface PipelineExecutionRootQuery_partitionSetsOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PipelineExecutionRootQuery_partitionSetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type PipelineExecutionRootQuery_partitionSetsOrError = PipelineExecutionRootQuery_partitionSetsOrError_PartitionSets | PipelineExecutionRootQuery_partitionSetsOrError_PipelineNotFoundError | PipelineExecutionRootQuery_partitionSetsOrError_PythonError;

export interface PipelineExecutionRootQuery {
  pipelineOrError: PipelineExecutionRootQuery_pipelineOrError;
  partitionSetsOrError: PipelineExecutionRootQuery_partitionSetsOrError;
}

export interface PipelineExecutionRootQueryVariables {
  pipelineName: string;
  repositoryName: string;
  repositoryLocationName: string;
}
