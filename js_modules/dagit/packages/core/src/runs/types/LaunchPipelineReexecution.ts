// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: LaunchPipelineReexecution
// ====================================================

export interface LaunchPipelineReexecution_launchPipelineReexecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "PipelineRunConflict" | "UnauthorizedError" | "PresetNotFoundError" | "ConflictingExecutionParamsError";
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_LaunchRunSuccess_run {
  __typename: "Run";
  id: string;
  runId: string;
  pipelineName: string;
  rootRunId: string | null;
  parentRunId: string | null;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_LaunchRunSuccess {
  __typename: "LaunchRunSuccess";
  run: LaunchPipelineReexecution_launchPipelineReexecution_LaunchRunSuccess_run;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_RunConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_RunConfigValidationInvalid {
  __typename: "RunConfigValidationInvalid";
  errors: LaunchPipelineReexecution_launchPipelineReexecution_RunConfigValidationInvalid_errors[];
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type LaunchPipelineReexecution_launchPipelineReexecution = LaunchPipelineReexecution_launchPipelineReexecution_InvalidStepError | LaunchPipelineReexecution_launchPipelineReexecution_LaunchRunSuccess | LaunchPipelineReexecution_launchPipelineReexecution_PipelineNotFoundError | LaunchPipelineReexecution_launchPipelineReexecution_RunConfigValidationInvalid | LaunchPipelineReexecution_launchPipelineReexecution_PythonError;

export interface LaunchPipelineReexecution {
  launchPipelineReexecution: LaunchPipelineReexecution_launchPipelineReexecution;
}

export interface LaunchPipelineReexecutionVariables {
  executionParams: ExecutionParams;
}
