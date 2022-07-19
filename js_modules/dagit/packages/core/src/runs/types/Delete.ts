/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: Delete
// ====================================================

export interface Delete_deletePipelineRun_DeletePipelineRunSuccess {
  __typename: "DeletePipelineRunSuccess";
}

export interface Delete_deletePipelineRun_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface Delete_deletePipelineRun_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: Delete_deletePipelineRun_PythonError_causes[];
}

export interface Delete_deletePipelineRun_UnauthorizedError {
  __typename: "UnauthorizedError";
  message: string;
}

export interface Delete_deletePipelineRun_RunNotFoundError {
  __typename: "RunNotFoundError";
  message: string;
}

export type Delete_deletePipelineRun = Delete_deletePipelineRun_DeletePipelineRunSuccess | Delete_deletePipelineRun_PythonError | Delete_deletePipelineRun_UnauthorizedError | Delete_deletePipelineRun_RunNotFoundError;

export interface Delete {
  deletePipelineRun: Delete_deletePipelineRun;
}

export interface DeleteVariables {
  runId: string;
}
