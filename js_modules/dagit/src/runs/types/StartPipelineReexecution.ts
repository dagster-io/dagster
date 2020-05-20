// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartPipelineReexecution
// ====================================================

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineRunDisabledError {
  __typename: "StartPipelineRunDisabledError" | "InvalidStepError" | "InvalidOutputError" | "PipelineRunConflict";
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess_run_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess_run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess_run_pipeline;
  tags: StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess_run_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
}

export interface StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess {
  __typename: "StartPipelineRunSuccess";
  run: StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess_run;
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

export type StartPipelineReexecution_startPipelineReexecution = StartPipelineReexecution_startPipelineReexecution_StartPipelineRunDisabledError | StartPipelineReexecution_startPipelineReexecution_StartPipelineRunSuccess | StartPipelineReexecution_startPipelineReexecution_PipelineNotFoundError | StartPipelineReexecution_startPipelineReexecution_PipelineConfigValidationInvalid | StartPipelineReexecution_startPipelineReexecution_PythonError;

export interface StartPipelineReexecution {
  startPipelineReexecution: StartPipelineReexecution_startPipelineReexecution;
}

export interface StartPipelineReexecutionVariables {
  executionParams: ExecutionParams;
}
