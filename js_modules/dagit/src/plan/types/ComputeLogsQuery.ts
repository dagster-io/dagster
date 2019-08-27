// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ComputeLogsQuery
// ====================================================

export interface ComputeLogsQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
}

export interface ComputeLogsQuery_pipelineRunOrError_PipelineRun_computeLogs {
  __typename: "ComputeLogs";
  stdout: string;
  stderr: string;
  cursor: any | null;
}

export interface ComputeLogsQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  runId: string;
  computeLogs: ComputeLogsQuery_pipelineRunOrError_PipelineRun_computeLogs;
}

export type ComputeLogsQuery_pipelineRunOrError = ComputeLogsQuery_pipelineRunOrError_PipelineRunNotFoundError | ComputeLogsQuery_pipelineRunOrError_PipelineRun;

export interface ComputeLogsQuery {
  pipelineRunOrError: ComputeLogsQuery_pipelineRunOrError;
}

export interface ComputeLogsQueryVariables {
  runId: string;
  stepKey: string;
}
