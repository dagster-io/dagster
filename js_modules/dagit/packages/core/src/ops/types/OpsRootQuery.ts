/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: OpsRootQuery
// ====================================================

export interface OpsRootQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions_type;
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions_type;
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
  outputDefinitions: OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_outputDefinitions[];
  inputDefinitions: OpsRootQuery_repositoryOrError_Repository_usedSolids_definition_inputDefinitions[];
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  name: string;
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids_invocations {
  __typename: "NodeInvocationSite";
  pipeline: OpsRootQuery_repositoryOrError_Repository_usedSolids_invocations_pipeline;
}

export interface OpsRootQuery_repositoryOrError_Repository_usedSolids {
  __typename: "UsedSolid";
  definition: OpsRootQuery_repositoryOrError_Repository_usedSolids_definition;
  invocations: OpsRootQuery_repositoryOrError_Repository_usedSolids_invocations[];
}

export interface OpsRootQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolids: OpsRootQuery_repositoryOrError_Repository_usedSolids[];
}

export type OpsRootQuery_repositoryOrError = OpsRootQuery_repositoryOrError_PythonError | OpsRootQuery_repositoryOrError_Repository;

export interface OpsRootQuery {
  repositoryOrError: OpsRootQuery_repositoryOrError;
}

export interface OpsRootQueryVariables {
  repositorySelector: RepositorySelector;
}
