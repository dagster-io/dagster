// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionSelector, ReexecutionConfig } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ReexecuteStep
// ====================================================

export interface ReexecuteStep_startPipelineExecution_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError";
}

export interface ReexecuteStep_startPipelineExecution_StartPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
}

export interface ReexecuteStep_startPipelineExecution_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: ReexecuteStep_startPipelineExecution_StartPipelineExecutionSuccess_run;
}

export interface ReexecuteStep_startPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface ReexecuteStep_startPipelineExecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface ReexecuteStep_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ReexecuteStep_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export type ReexecuteStep_startPipelineExecution = ReexecuteStep_startPipelineExecution_InvalidStepError | ReexecuteStep_startPipelineExecution_StartPipelineExecutionSuccess | ReexecuteStep_startPipelineExecution_PipelineNotFoundError | ReexecuteStep_startPipelineExecution_PipelineConfigValidationInvalid;

export interface ReexecuteStep {
  startPipelineExecution: ReexecuteStep_startPipelineExecution;
}

export interface ReexecuteStepVariables {
  pipeline: ExecutionSelector;
  environmentConfigData: any;
  mode: string;
  stepKeys?: string[] | null;
  reexecutionConfig?: ReexecutionConfig | null;
}
