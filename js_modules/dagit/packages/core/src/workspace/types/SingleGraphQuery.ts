/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { GraphSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleGraphQuery
// ====================================================

export interface SingleGraphQuery_graphOrError_GraphNotFoundError {
  __typename: "GraphNotFoundError" | "PythonError";
}

export interface SingleGraphQuery_graphOrError_Graph {
  __typename: "Graph";
  id: string;
  name: string;
  description: string | null;
}

export type SingleGraphQuery_graphOrError = SingleGraphQuery_graphOrError_GraphNotFoundError | SingleGraphQuery_graphOrError_Graph;

export interface SingleGraphQuery {
  graphOrError: SingleGraphQuery_graphOrError;
}

export interface SingleGraphQueryVariables {
  selector: GraphSelector;
}
