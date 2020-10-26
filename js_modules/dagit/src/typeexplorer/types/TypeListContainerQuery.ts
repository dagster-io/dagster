// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: TypeListContainerQuery
// ====================================================

export interface TypeListContainerQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline_dagsterTypes {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  dagsterTypes: TypeListContainerQuery_pipelineOrError_Pipeline_dagsterTypes[];
}

export type TypeListContainerQuery_pipelineOrError = TypeListContainerQuery_pipelineOrError_PipelineNotFoundError | TypeListContainerQuery_pipelineOrError_Pipeline;

export interface TypeListContainerQuery {
  pipelineOrError: TypeListContainerQuery_pipelineOrError;
}

export interface TypeListContainerQueryVariables {
  pipelineSelector: PipelineSelector;
}
