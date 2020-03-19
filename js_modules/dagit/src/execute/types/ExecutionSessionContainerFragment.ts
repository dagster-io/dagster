// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ExecutionSessionContainerFragment
// ====================================================

export interface ExecutionSessionContainerFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PythonError";
}

export interface ExecutionSessionContainerFragment_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface ExecutionSessionContainerFragment_Pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ExecutionSessionContainerFragment_Pipeline {
  __typename: "Pipeline";
  name: string;
  modes: ExecutionSessionContainerFragment_Pipeline_modes[];
  tags: ExecutionSessionContainerFragment_Pipeline_tags[];
}

export interface ExecutionSessionContainerFragment_InvalidSubsetError_pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface ExecutionSessionContainerFragment_InvalidSubsetError_pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ExecutionSessionContainerFragment_InvalidSubsetError_pipeline {
  __typename: "Pipeline";
  name: string;
  modes: ExecutionSessionContainerFragment_InvalidSubsetError_pipeline_modes[];
  tags: ExecutionSessionContainerFragment_InvalidSubsetError_pipeline_tags[];
}

export interface ExecutionSessionContainerFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
  pipeline: ExecutionSessionContainerFragment_InvalidSubsetError_pipeline;
}

export type ExecutionSessionContainerFragment = ExecutionSessionContainerFragment_PipelineNotFoundError | ExecutionSessionContainerFragment_Pipeline | ExecutionSessionContainerFragment_InvalidSubsetError;
