/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryResourcesListQuery
// ====================================================

export interface RepositoryResourcesListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_definition_SolidDefinition {
  __typename: "SolidDefinition";
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  id: string;
  name: string;
  description: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_definition = RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_definition_SolidDefinition | RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_definition_CompositeSolidDefinition;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_invocations_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "NodeInvocationSite";
  pipeline: RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
  solidHandle: RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_invocations_solidHandle;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  name: string;
  isJob: boolean;
  graphName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: RepositoryResourcesListQuery_repositoryOrError_Repository_usedSolids[];
  pipelines: RepositoryResourcesListQuery_repositoryOrError_Repository_pipelines[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositoryResourcesListQuery_repositoryOrError = RepositoryResourcesListQuery_repositoryOrError_PythonError | RepositoryResourcesListQuery_repositoryOrError_Repository | RepositoryResourcesListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositoryResourcesListQuery {
  repositoryOrError: RepositoryResourcesListQuery_repositoryOrError;
}

export interface RepositoryResourcesListQueryVariables {
  repositorySelector: RepositorySelector;
}
