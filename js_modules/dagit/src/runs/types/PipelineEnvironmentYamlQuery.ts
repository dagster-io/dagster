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

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  id: string;
  pipeline: PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun_pipeline;
  pipelineSnapshotId: string | null;
  runConfigYaml: string;
  repositoryOrigin: PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun_repositoryOrigin | null;
}

export type PipelineEnvironmentYamlQuery_pipelineRunOrError = PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRunNotFoundError | PipelineEnvironmentYamlQuery_pipelineRunOrError_PipelineRun;

export interface PipelineEnvironmentYamlQuery {
  pipelineRunOrError: PipelineEnvironmentYamlQuery_pipelineRunOrError;
}

export interface PipelineEnvironmentYamlQueryVariables {
  runId: string;
}
