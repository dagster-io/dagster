// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionParams, ReexecutionConfig } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: Reexecute
// ====================================================

export interface Reexecute_startPipelineExecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "PythonError";
}

export interface Reexecute_startPipelineExecution_StartPipelineExecutionSuccess_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface Reexecute_startPipelineExecution_StartPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: Reexecute_startPipelineExecution_StartPipelineExecutionSuccess_run_pipeline;
}

export interface Reexecute_startPipelineExecution_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: Reexecute_startPipelineExecution_StartPipelineExecutionSuccess_run;
}

export interface Reexecute_startPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface Reexecute_startPipelineExecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface Reexecute_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: Reexecute_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export type Reexecute_startPipelineExecution = Reexecute_startPipelineExecution_InvalidStepError | Reexecute_startPipelineExecution_StartPipelineExecutionSuccess | Reexecute_startPipelineExecution_PipelineNotFoundError | Reexecute_startPipelineExecution_PipelineConfigValidationInvalid;

export interface Reexecute {
  startPipelineExecution: Reexecute_startPipelineExecution;
}

export interface ReexecuteVariables {
  executionParams: ExecutionParams;
  reexecutionConfig?: ReexecutionConfig | null;
}
