/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpNodeOutputDefinition
// ====================================================

export interface OpNodeOutputDefinition_type {
  __typename: "ListDagsterType" | "NullableDagsterType" | "RegularDagsterType";
  displayName: string;
}

export interface OpNodeOutputDefinition {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpNodeOutputDefinition_type;
}
