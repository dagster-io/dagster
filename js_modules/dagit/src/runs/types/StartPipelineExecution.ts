// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartPipelineExecution
// ====================================================

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionDisabledError {
  __typename: "StartPipelineExecutionDisabledError" | "InvalidStepError" | "InvalidOutputError";
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_pipeline;
  tags: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_tags[];
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run;
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

export type StartPipelineExecution_startPipelineExecution = StartPipelineExecution_startPipelineExecution_StartPipelineExecutionDisabledError | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess | StartPipelineExecution_startPipelineExecution_PipelineNotFoundError | StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid | StartPipelineExecution_startPipelineExecution_PythonError;

export interface StartPipelineExecution {
  startPipelineExecution: StartPipelineExecution_startPipelineExecution;
}

export interface StartPipelineExecutionVariables {
  executionParams: ExecutionParams;
}
