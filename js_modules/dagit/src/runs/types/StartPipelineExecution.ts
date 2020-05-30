// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartPipelineExecution
// ====================================================

export interface StartPipelineExecution_startPipelineExecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "PipelineRunConflict";
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess_run_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess_run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess_run_pipeline;
  tags: StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess_run_tags[];
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess {
  __typename: "StartPipelineRunSuccess";
  run: StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess_run;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export interface StartPipelineExecution_startPipelineExecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StartPipelineExecution_startPipelineExecution = StartPipelineExecution_startPipelineExecution_InvalidStepError | StartPipelineExecution_startPipelineExecution_StartPipelineRunSuccess | StartPipelineExecution_startPipelineExecution_PipelineNotFoundError | StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid | StartPipelineExecution_startPipelineExecution_PythonError;

export interface StartPipelineExecution {
  startPipelineExecution: StartPipelineExecution_startPipelineExecution;
}

export interface StartPipelineExecutionVariables {
  executionParams: ExecutionParams;
}
