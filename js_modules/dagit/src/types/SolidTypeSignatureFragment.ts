// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidTypeSignatureFragment
// ====================================================

export interface SolidTypeSignatureFragment_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidTypeSignatureFragment_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidTypeSignatureFragment_outputDefinitions_type;
}

export interface SolidTypeSignatureFragment_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidTypeSignatureFragment_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidTypeSignatureFragment_inputDefinitions_type;
}

export interface SolidTypeSignatureFragment {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  outputDefinitions: SolidTypeSignatureFragment_outputDefinitions[];
  inputDefinitions: SolidTypeSignatureFragment_inputDefinitions[];
}
