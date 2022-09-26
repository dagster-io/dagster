/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceGraphsQuery
// ====================================================

export interface WorkspaceGraphsQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_definition_SolidDefinition {
  __typename: "SolidDefinition";
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  id: string;
  name: string;
  description: string | null;
}

export type WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_definition = WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_definition_SolidDefinition | WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_definition_CompositeSolidDefinition;

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_invocations_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "NodeInvocationSite";
  pipeline: WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
  solidHandle: WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_invocations_solidHandle;
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  graphName: string;
}

export interface WorkspaceGraphsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: WorkspaceGraphsQuery_repositoryOrError_Repository_usedSolids[];
  pipelines: WorkspaceGraphsQuery_repositoryOrError_Repository_pipelines[];
}

export interface WorkspaceGraphsQuery_repositoryOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceGraphsQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceGraphsQuery_repositoryOrError_PythonError_causes[];
}

export type WorkspaceGraphsQuery_repositoryOrError = WorkspaceGraphsQuery_repositoryOrError_RepositoryNotFoundError | WorkspaceGraphsQuery_repositoryOrError_Repository | WorkspaceGraphsQuery_repositoryOrError_PythonError;

export interface WorkspaceGraphsQuery {
  repositoryOrError: WorkspaceGraphsQuery_repositoryOrError;
}

export interface WorkspaceGraphsQueryVariables {
  selector: RepositorySelector;
}
