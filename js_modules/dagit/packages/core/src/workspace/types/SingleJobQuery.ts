/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleJobQuery
// ====================================================

export interface SingleJobQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface SingleJobQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  description: string | null;
}

export type SingleJobQuery_pipelineOrError = SingleJobQuery_pipelineOrError_PipelineNotFoundError | SingleJobQuery_pipelineOrError_Pipeline;

export interface SingleJobQuery {
  pipelineOrError: SingleJobQuery_pipelineOrError;
}

export interface SingleJobQueryVariables {
  selector: PipelineSelector;
}
