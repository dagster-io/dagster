/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ExecutionSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartPipelineExecution
// ====================================================

export interface StartPipelineExecution_startPipelineExecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError";
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
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
  __typename: "FieldNotDefinedConfigError" | "MissingFieldConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export type StartPipelineExecution_startPipelineExecution = StartPipelineExecution_startPipelineExecution_InvalidStepError | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess | StartPipelineExecution_startPipelineExecution_PipelineNotFoundError | StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid;

export interface StartPipelineExecution {
  startPipelineExecution: StartPipelineExecution_startPipelineExecution;
}

export interface StartPipelineExecutionVariables {
  pipeline: ExecutionSelector;
  config: any;
}
