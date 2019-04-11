/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RootPipelinesQuery
// ====================================================

export interface RootPipelinesQuery_pipelinesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootPipelinesQuery_pipelinesOrError_InvalidDefinitionError {
  __typename: "InvalidDefinitionError";
  message: string;
  stack: string[];
}

export interface RootPipelinesQuery_pipelinesOrError_PipelineConnection_nodes {
  __typename: "Pipeline";
  name: string;
}

export interface RootPipelinesQuery_pipelinesOrError_PipelineConnection {
  __typename: "PipelineConnection";
  nodes: RootPipelinesQuery_pipelinesOrError_PipelineConnection_nodes[];
}

export type RootPipelinesQuery_pipelinesOrError = RootPipelinesQuery_pipelinesOrError_PythonError | RootPipelinesQuery_pipelinesOrError_InvalidDefinitionError | RootPipelinesQuery_pipelinesOrError_PipelineConnection;

export interface RootPipelinesQuery {
  pipelinesOrError: RootPipelinesQuery_pipelinesOrError;
}
