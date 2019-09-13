// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: HandleStartExecutionFragment
// ====================================================

export interface HandleStartExecutionFragment_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError";
}

export interface HandleStartExecutionFragment_StartPipelineExecutionSuccess_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface HandleStartExecutionFragment_StartPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: HandleStartExecutionFragment_StartPipelineExecutionSuccess_run_pipeline;
}

export interface HandleStartExecutionFragment_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: HandleStartExecutionFragment_StartPipelineExecutionSuccess_run;
}

export interface HandleStartExecutionFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface HandleStartExecutionFragment_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface HandleStartExecutionFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: HandleStartExecutionFragment_PipelineConfigValidationInvalid_errors[];
}

export type HandleStartExecutionFragment = HandleStartExecutionFragment_InvalidStepError | HandleStartExecutionFragment_StartPipelineExecutionSuccess | HandleStartExecutionFragment_PipelineNotFoundError | HandleStartExecutionFragment_PipelineConfigValidationInvalid;
