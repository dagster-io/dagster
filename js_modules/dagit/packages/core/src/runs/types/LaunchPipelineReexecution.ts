/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExecutionParams, ReexecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: LaunchPipelineReexecution
// ====================================================

export interface LaunchPipelineReexecution_launchPipelineReexecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "RunConflict" | "UnauthorizedError" | "PresetNotFoundError" | "ConflictingExecutionParamsError" | "NoModeProvidedError";
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

export interface LaunchPipelineReexecution_launchPipelineReexecution_InvalidSubsetError {
  __typename: "InvalidSubsetError";
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

export interface LaunchPipelineReexecution_launchPipelineReexecution_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LaunchPipelineReexecution_launchPipelineReexecution_PythonError_causes[];
}

export type LaunchPipelineReexecution_launchPipelineReexecution = LaunchPipelineReexecution_launchPipelineReexecution_InvalidStepError | LaunchPipelineReexecution_launchPipelineReexecution_LaunchRunSuccess | LaunchPipelineReexecution_launchPipelineReexecution_PipelineNotFoundError | LaunchPipelineReexecution_launchPipelineReexecution_InvalidSubsetError | LaunchPipelineReexecution_launchPipelineReexecution_RunConfigValidationInvalid | LaunchPipelineReexecution_launchPipelineReexecution_PythonError;

export interface LaunchPipelineReexecution {
  launchPipelineReexecution: LaunchPipelineReexecution_launchPipelineReexecution;
}

export interface LaunchPipelineReexecutionVariables {
  executionParams?: ExecutionParams | null;
  reexecutionParams?: ReexecutionParams | null;
}
