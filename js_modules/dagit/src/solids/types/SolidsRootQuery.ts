// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SolidsRootQuery
// ====================================================

export interface SolidsRootQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions_type;
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions_type;
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
  outputDefinitions: SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions[];
  inputDefinitions: SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions[];
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "SolidInvocationSite";
  pipeline: SolidsRootQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
}

export interface SolidsRootQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: SolidsRootQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: SolidsRootQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface SolidsRootQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: SolidsRootQuery_repositoryOrError_Repository_usedSolids[];
}

export type SolidsRootQuery_repositoryOrError = SolidsRootQuery_repositoryOrError_PythonError | SolidsRootQuery_repositoryOrError_Repository;

export interface SolidsRootQuery {
  repositoryOrError: SolidsRootQuery_repositoryOrError;
}

export interface SolidsRootQueryVariables {
  repositorySelector: RepositorySelector;
}
