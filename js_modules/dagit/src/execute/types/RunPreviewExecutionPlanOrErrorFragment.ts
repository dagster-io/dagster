// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunPreviewExecutionPlanOrErrorFragment
// ====================================================

export interface RunPreviewExecutionPlanOrErrorFragment_ExecutionPlan {
  __typename: "ExecutionPlan" | "PipelineConfigValidationInvalid";
}

export interface RunPreviewExecutionPlanOrErrorFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface RunPreviewExecutionPlanOrErrorFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface RunPreviewExecutionPlanOrErrorFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPreviewExecutionPlanOrErrorFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPreviewExecutionPlanOrErrorFragment_PythonError_cause | null;
}

export type RunPreviewExecutionPlanOrErrorFragment = RunPreviewExecutionPlanOrErrorFragment_ExecutionPlan | RunPreviewExecutionPlanOrErrorFragment_PipelineNotFoundError | RunPreviewExecutionPlanOrErrorFragment_InvalidSubsetError | RunPreviewExecutionPlanOrErrorFragment_PythonError;
