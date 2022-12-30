/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpNodeInputDefinition
// ====================================================

export interface OpNodeInputDefinition_type {
  __typename: "ListDagsterType" | "NullableDagsterType" | "RegularDagsterType";
  displayName: string;
}

export interface OpNodeInputDefinition {
  __typename: "InputDefinition";
  name: string;
  type: OpNodeInputDefinition_type;
}
