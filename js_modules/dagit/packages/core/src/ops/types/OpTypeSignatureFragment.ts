/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpTypeSignatureFragment
// ====================================================

export interface OpTypeSignatureFragment_outputDefinitions_type {
  __typename: "ListDagsterType" | "NullableDagsterType" | "RegularDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface OpTypeSignatureFragment_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: OpTypeSignatureFragment_outputDefinitions_type;
}

export interface OpTypeSignatureFragment_inputDefinitions_type {
  __typename: "ListDagsterType" | "NullableDagsterType" | "RegularDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface OpTypeSignatureFragment_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpTypeSignatureFragment_inputDefinitions_type;
}

export interface OpTypeSignatureFragment {
  __typename: "CompositeSolidDefinition" | "SolidDefinition";
  outputDefinitions: OpTypeSignatureFragment_outputDefinitions[];
  inputDefinitions: OpTypeSignatureFragment_inputDefinitions[];
}
