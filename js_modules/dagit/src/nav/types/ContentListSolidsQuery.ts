// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ContentListSolidsQuery
// ====================================================

export interface ContentListSolidsQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface ContentListSolidsQuery_repositoryOrError_Repository_usedSolids_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
}

export interface ContentListSolidsQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface ContentListSolidsQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "SolidInvocationSite";
  pipeline: ContentListSolidsQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
}

export interface ContentListSolidsQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: ContentListSolidsQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: ContentListSolidsQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface ContentListSolidsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: ContentListSolidsQuery_repositoryOrError_Repository_usedSolids[];
}

export type ContentListSolidsQuery_repositoryOrError = ContentListSolidsQuery_repositoryOrError_PythonError | ContentListSolidsQuery_repositoryOrError_Repository;

export interface ContentListSolidsQuery {
  repositoryOrError: ContentListSolidsQuery_repositoryOrError;
}

export interface ContentListSolidsQueryVariables {
  repositorySelector: RepositorySelector;
}
