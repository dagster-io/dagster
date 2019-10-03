// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: Cancel
// ====================================================

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess {
  __typename: "CancelPipelineExecutionSuccess";
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionFailure {
  __typename: "CancelPipelineExecutionFailure";
  message: string;
}

export interface Cancel_cancelPipelineExecution_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export type Cancel_cancelPipelineExecution = Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess | Cancel_cancelPipelineExecution_CancelPipelineExecutionFailure | Cancel_cancelPipelineExecution_PipelineRunNotFoundError;

export interface Cancel {
  cancelPipelineExecution: Cancel_cancelPipelineExecution;
}

export interface CancelVariables {
  runId: string;
}
