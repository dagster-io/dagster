/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: LaunchPipelineExecution
// ====================================================

export interface LaunchPipelineExecution_launchPipelineExecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "RunConflict" | "UnauthorizedError" | "PresetNotFoundError" | "ConflictingExecutionParamsError" | "NoModeProvidedError";
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

export interface LaunchPipelineExecution_launchPipelineExecution_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface LaunchPipelineExecution_launchPipelineExecution_RunConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface LaunchPipelineExecution_launchPipelineExecution_RunConfigValidationInvalid {
  __typename: "RunConfigValidationInvalid";
  errors: LaunchPipelineExecution_launchPipelineExecution_RunConfigValidationInvalid_errors[];
}

export interface LaunchPipelineExecution_launchPipelineExecution_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchPipelineExecution_launchPipelineExecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LaunchPipelineExecution_launchPipelineExecution_PythonError_causes[];
}

export type LaunchPipelineExecution_launchPipelineExecution = LaunchPipelineExecution_launchPipelineExecution_InvalidStepError | LaunchPipelineExecution_launchPipelineExecution_LaunchRunSuccess | LaunchPipelineExecution_launchPipelineExecution_PipelineNotFoundError | LaunchPipelineExecution_launchPipelineExecution_InvalidSubsetError | LaunchPipelineExecution_launchPipelineExecution_RunConfigValidationInvalid | LaunchPipelineExecution_launchPipelineExecution_PythonError;

export interface LaunchPipelineExecution {
  launchPipelineExecution: LaunchPipelineExecution_launchPipelineExecution;
}

export interface LaunchPipelineExecutionVariables {
  executionParams: ExecutionParams;
}
