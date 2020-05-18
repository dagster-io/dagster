// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ContentListSolidsQuery
// ====================================================

export interface ContentListSolidsQuery_usedSolids_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
}

export interface ContentListSolidsQuery_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface ContentListSolidsQuery_usedSolids_invocations {
  __typename: "SolidInvocationSite";
  pipeline: ContentListSolidsQuery_usedSolids_invocations_pipeline;
}

export interface ContentListSolidsQuery_usedSolids {
  __typename: "UsedSolid";
  definition: ContentListSolidsQuery_usedSolids_definition;
  invocations: ContentListSolidsQuery_usedSolids_invocations[];
}

export interface ContentListSolidsQuery {
  usedSolids: ContentListSolidsQuery_usedSolids[];
}
