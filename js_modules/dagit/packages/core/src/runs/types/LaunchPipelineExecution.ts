// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: LaunchPipelineExecution
// ====================================================

export interface LaunchPipelineExecution_launchPipelineExecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "PipelineRunConflict" | "UnauthorizedError" | "PresetNotFoundError" | "ConflictingExecutionParamsError";
}

export interface LaunchPipelineExecution_launchPipelineExecution_LaunchRunSuccess_run {
  __typename: "Run";
  id: string;
  runId: string;
  pipelineName: string;
}

export interface LaunchPipelineExecution_launchPipelineExecution_LaunchRunSuccess {
  __typename: "LaunchRunSuccess";
  run: LaunchPipelineExecution_launchPipelineExecution_LaunchRunSuccess_run;
}

export interface LaunchPipelineExecution_launchPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface LaunchPipelineExecution_launchPipelineExecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface LaunchPipelineExecution_launchPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: LaunchPipelineExecution_launchPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export interface LaunchPipelineExecution_launchPipelineExecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type LaunchPipelineExecution_launchPipelineExecution = LaunchPipelineExecution_launchPipelineExecution_InvalidStepError | LaunchPipelineExecution_launchPipelineExecution_LaunchRunSuccess | LaunchPipelineExecution_launchPipelineExecution_PipelineNotFoundError | LaunchPipelineExecution_launchPipelineExecution_PipelineConfigValidationInvalid | LaunchPipelineExecution_launchPipelineExecution_PythonError;

export interface LaunchPipelineExecution {
  launchPipelineExecution: LaunchPipelineExecution_launchPipelineExecution;
}

export interface LaunchPipelineExecutionVariables {
  executionParams: ExecutionParams;
}
