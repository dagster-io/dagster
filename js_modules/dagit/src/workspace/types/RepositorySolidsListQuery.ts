// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositorySolidsListQuery
// ====================================================

export interface RepositorySolidsListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  description: string | null;
  name: string;
}

export interface RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "SolidInvocationSite";
  pipeline: RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
}

export interface RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface RepositorySolidsListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: RepositorySolidsListQuery_repositoryOrError_Repository_usedSolids[];
}

export interface RepositorySolidsListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositorySolidsListQuery_repositoryOrError = RepositorySolidsListQuery_repositoryOrError_PythonError | RepositorySolidsListQuery_repositoryOrError_Repository | RepositorySolidsListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositorySolidsListQuery {
  repositoryOrError: RepositorySolidsListQuery_repositoryOrError;
}

export interface RepositorySolidsListQueryVariables {
  repositorySelector: RepositorySelector;
}
