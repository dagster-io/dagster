// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerFragment
// ====================================================

export interface PipelineExecutionContainerFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PythonError";
}

export interface PipelineExecutionContainerFragment_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_Pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionContainerFragment_Pipeline_modes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_modes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
  pipeline: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline;
}

export type PipelineExecutionContainerFragment = PipelineExecutionContainerFragment_PipelineNotFoundError | PipelineExecutionContainerFragment_Pipeline | PipelineExecutionContainerFragment_InvalidSubsetError;
