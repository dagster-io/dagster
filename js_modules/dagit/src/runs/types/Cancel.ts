// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: Cancel
// ====================================================

export interface Cancel_terminatePipelineExecution_TerminatePipelineExecutionFailure {
  __typename: "TerminatePipelineExecutionFailure";
  message: string;
}

export interface Cancel_terminatePipelineExecution_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export interface Cancel_terminatePipelineExecution_TerminatePipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  canTerminate: boolean;
}

export interface Cancel_terminatePipelineExecution_TerminatePipelineExecutionSuccess {
  __typename: "TerminatePipelineExecutionSuccess";
  run: Cancel_terminatePipelineExecution_TerminatePipelineExecutionSuccess_run;
}

export interface Cancel_terminatePipelineExecution_PythonError {
  __typename: "PythonError";
  message: string;
}

export type Cancel_terminatePipelineExecution = Cancel_terminatePipelineExecution_TerminatePipelineExecutionFailure | Cancel_terminatePipelineExecution_PipelineRunNotFoundError | Cancel_terminatePipelineExecution_TerminatePipelineExecutionSuccess | Cancel_terminatePipelineExecution_PythonError;

export interface Cancel {
  terminatePipelineExecution: Cancel_terminatePipelineExecution;
}

export interface CancelVariables {
  runId: string;
}
