// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartPipelineReexecution
// ====================================================

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionDisabledError {
  __typename: "StartPipelineReexecutionDisabledError" | "InvalidStepError" | "InvalidOutputError" | "PipelineRunConflict";
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess_run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess_run_pipeline;
  tags: StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess_run_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess {
  __typename: "StartPipelineReexecutionSuccess";
  run: StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess_run;
}

export interface StartPipelineReexecution_startPipelineReexecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface StartPipelineReexecution_startPipelineReexecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface StartPipelineReexecution_startPipelineReexecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: StartPipelineReexecution_startPipelineReexecution_PipelineConfigValidationInvalid_errors[];
}

export interface StartPipelineReexecution_startPipelineReexecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StartPipelineReexecution_startPipelineReexecution = StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionDisabledError | StartPipelineReexecution_startPipelineReexecution_StartPipelineReexecutionSuccess | StartPipelineReexecution_startPipelineReexecution_PipelineNotFoundError | StartPipelineReexecution_startPipelineReexecution_PipelineConfigValidationInvalid | StartPipelineReexecution_startPipelineReexecution_PythonError;

export interface StartPipelineReexecution {
  startPipelineReexecution: StartPipelineReexecution_startPipelineReexecution;
}

export interface StartPipelineReexecutionVariables {
  executionParams: ExecutionParams;
}
