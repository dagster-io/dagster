/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: LaunchpadRootQuery
// ====================================================

export interface LaunchpadRootQuery_pipelineOrError_InvalidSubsetError {
  __typename: "InvalidSubsetError";
}

export interface LaunchpadRootQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface LaunchpadRootQuery_pipelineOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchpadRootQuery_pipelineOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LaunchpadRootQuery_pipelineOrError_PythonError_causes[];
}

export interface LaunchpadRootQuery_pipelineOrError_Pipeline_presets_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchpadRootQuery_pipelineOrError_Pipeline_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: LaunchpadRootQuery_pipelineOrError_Pipeline_presets_tags[];
}

export interface LaunchpadRootQuery_pipelineOrError_Pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchpadRootQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
}

export interface LaunchpadRootQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  isAssetJob: boolean;
  name: string;
  presets: LaunchpadRootQuery_pipelineOrError_Pipeline_presets[];
  tags: LaunchpadRootQuery_pipelineOrError_Pipeline_tags[];
  modes: LaunchpadRootQuery_pipelineOrError_Pipeline_modes[];
}

export type LaunchpadRootQuery_pipelineOrError = LaunchpadRootQuery_pipelineOrError_InvalidSubsetError | LaunchpadRootQuery_pipelineOrError_PipelineNotFoundError | LaunchpadRootQuery_pipelineOrError_PythonError | LaunchpadRootQuery_pipelineOrError_Pipeline;

export interface LaunchpadRootQuery_partitionSetsOrError_PartitionSets_results {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface LaunchpadRootQuery_partitionSetsOrError_PartitionSets {
  __typename: "PartitionSets";
  results: LaunchpadRootQuery_partitionSetsOrError_PartitionSets_results[];
}

export interface LaunchpadRootQuery_partitionSetsOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface LaunchpadRootQuery_partitionSetsOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchpadRootQuery_partitionSetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LaunchpadRootQuery_partitionSetsOrError_PythonError_causes[];
}

export type LaunchpadRootQuery_partitionSetsOrError = LaunchpadRootQuery_partitionSetsOrError_PartitionSets | LaunchpadRootQuery_partitionSetsOrError_PipelineNotFoundError | LaunchpadRootQuery_partitionSetsOrError_PythonError;

export interface LaunchpadRootQuery {
  pipelineOrError: LaunchpadRootQuery_pipelineOrError;
  partitionSetsOrError: LaunchpadRootQuery_partitionSetsOrError;
}

export interface LaunchpadRootQueryVariables {
  pipelineName: string;
  repositoryName: string;
  repositoryLocationName: string;
}
