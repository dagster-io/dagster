// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineEnvironmentYamlQuery
// ====================================================

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  runConfigYaml: string;
}

export type PipelineEnvironmentYamlQuery_pipelineRunOrError = PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRunNotFoundError | PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun;

export interface PipelineEnvironmentYamlQuery {
  pipelineRunOrError: PipelineEnvironmentYamlQuery_pipelineRunOrError;
}

export interface PipelineEnvironmentYamlQueryVariables {
  runId: string;
}
