// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineEnvironmentYamlQuery
// ====================================================

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_Run_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  pipeline: PipelineEnvironmentYamlQuery_pipelineRunOrError_Run_pipeline;
  pipelineSnapshotId: string | null;
  runConfigYaml: string;
  repositoryOrigin: PipelineEnvironmentYamlQuery_pipelineRunOrError_Run_repositoryOrigin | null;
}

export type PipelineEnvironmentYamlQuery_pipelineRunOrError = PipelineEnvironmentYamlQuery_pipelineRunOrError_RunNotFoundError | PipelineEnvironmentYamlQuery_pipelineRunOrError_Run;

export interface PipelineEnvironmentYamlQuery {
  pipelineRunOrError: PipelineEnvironmentYamlQuery_pipelineRunOrError;
}

export interface PipelineEnvironmentYamlQueryVariables {
  runId: string;
}
