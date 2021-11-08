// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryGraphsListQuery
// ====================================================

export interface RepositoryGraphsListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_definition_SolidDefinition {
  __typename: "SolidDefinition";
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
}

export type RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_definition = RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_definition_SolidDefinition | RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_definition_CompositeSolidDefinition;

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_invocations_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "NodeInvocationSite";
  pipeline: RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
  solidHandle: RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_invocations_solidHandle;
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  name: string;
  isJob: boolean;
  graphName: string;
}

export interface RepositoryGraphsListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: RepositoryGraphsListQuery_repositoryOrError_Repository_usedSolids[];
  pipelines: RepositoryGraphsListQuery_repositoryOrError_Repository_pipelines[];
}

export interface RepositoryGraphsListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositoryGraphsListQuery_repositoryOrError = RepositoryGraphsListQuery_repositoryOrError_PythonError | RepositoryGraphsListQuery_repositoryOrError_Repository | RepositoryGraphsListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositoryGraphsListQuery {
  repositoryOrError: RepositoryGraphsListQuery_repositoryOrError;
}

export interface RepositoryGraphsListQueryVariables {
  repositorySelector: RepositorySelector;
}
