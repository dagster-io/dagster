// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: Delete
// ====================================================

export interface Delete_deletePipelineRun_DeletePipelineRunSuccess {
  __typename: "DeletePipelineRunSuccess";
}

export interface Delete_deletePipelineRun_PythonError {
  __typename: "PythonError";
  message: string;
}

export interface Delete_deletePipelineRun_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export type Delete_deletePipelineRun = Delete_deletePipelineRun_DeletePipelineRunSuccess | Delete_deletePipelineRun_PythonError | Delete_deletePipelineRun_PipelineRunNotFoundError;

export interface Delete {
  deletePipelineRun: Delete_deletePipelineRun;
}

export interface DeleteVariables {
  runId: string;
}
