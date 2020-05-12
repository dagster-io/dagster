// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SolidsRootQuery
// ====================================================

export interface SolidsRootQuery_usedSolids_definition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidsRootQuery_usedSolids_definition_outputDefinitions_type;
}

export interface SolidsRootQuery_usedSolids_definition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidsRootQuery_usedSolids_definition_inputDefinitions_type;
}

export interface SolidsRootQuery_usedSolids_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
  outputDefinitions: SolidsRootQuery_usedSolids_definition_outputDefinitions[];
  inputDefinitions: SolidsRootQuery_usedSolids_definition_inputDefinitions[];
}

export interface SolidsRootQuery_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface SolidsRootQuery_usedSolids_invocations {
  __typename: "SolidInvocationSite";
  pipeline: SolidsRootQuery_usedSolids_invocations_pipeline;
}

export interface SolidsRootQuery_usedSolids {
  __typename: "UsedSolid";
  definition: SolidsRootQuery_usedSolids_definition;
  invocations: SolidsRootQuery_usedSolids_invocations[];
}

export interface SolidsRootQuery {
  usedSolids: SolidsRootQuery_usedSolids[];
}
