// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RunsSearchSpaceQuery
// ====================================================

export interface RunsSearchSpaceQuery_pipelinesOrError_PythonError {
  __typename: "PythonError";
}

export interface RunsSearchSpaceQuery_pipelinesOrError_PipelineConnection_nodes {
  __typename: "Pipeline";
  name: string;
}

export interface RunsSearchSpaceQuery_pipelinesOrError_PipelineConnection {
  __typename: "PipelineConnection";
  nodes: RunsSearchSpaceQuery_pipelinesOrError_PipelineConnection_nodes[];
}

export type RunsSearchSpaceQuery_pipelinesOrError = RunsSearchSpaceQuery_pipelinesOrError_PythonError | RunsSearchSpaceQuery_pipelinesOrError_PipelineConnection;

export interface RunsSearchSpaceQuery_pipelineRunTags {
  __typename: "PipelineTagAndValues";
  key: string;
  values: string[];
}

export interface RunsSearchSpaceQuery {
  pipelinesOrError: RunsSearchSpaceQuery_pipelinesOrError;
  pipelineRunTags: RunsSearchSpaceQuery_pipelineRunTags[];
}
