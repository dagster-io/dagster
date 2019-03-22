/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeListContainerQuery
// ====================================================

export interface TypeListContainerQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "PipelineNotFoundError" | "SolidNotFoundError";
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline_runtimeTypes {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  runtimeTypes: TypeListContainerQuery_pipelineOrError_Pipeline_runtimeTypes[];
}

export type TypeListContainerQuery_pipelineOrError = TypeListContainerQuery_pipelineOrError_PythonError | TypeListContainerQuery_pipelineOrError_Pipeline;

export interface TypeListContainerQuery {
  pipelineOrError: TypeListContainerQuery_pipelineOrError;
}

export interface TypeListContainerQueryVariables {
  pipelineName: string;
}
