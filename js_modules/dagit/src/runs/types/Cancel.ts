// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: Cancel
// ====================================================

export interface Cancel_cancelPipelineExecution_PythonError {
  __typename: "PythonError";
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionFailure {
  __typename: "CancelPipelineExecutionFailure";
  message: string;
}

export interface Cancel_cancelPipelineExecution_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  canCancel: boolean;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess {
  __typename: "CancelPipelineExecutionSuccess";
  run: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run;
}

export type Cancel_cancelPipelineExecution = Cancel_cancelPipelineExecution_PythonError | Cancel_cancelPipelineExecution_CancelPipelineExecutionFailure | Cancel_cancelPipelineExecution_PipelineRunNotFoundError | Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess;

export interface Cancel {
  cancelPipelineExecution: Cancel_cancelPipelineExecution;
}

export interface CancelVariables {
  runId: string;
}
