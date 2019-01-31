/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidTypeSignatureFragment
// ====================================================

export interface SolidTypeSignatureFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidTypeSignatureFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidTypeSignatureFragment_outputs_definition_type;
}

export interface SolidTypeSignatureFragment_outputs {
  __typename: "Output";
  definition: SolidTypeSignatureFragment_outputs_definition;
}

export interface SolidTypeSignatureFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SolidTypeSignatureFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidTypeSignatureFragment_inputs_definition_type;
}

export interface SolidTypeSignatureFragment_inputs {
  __typename: "Input";
  definition: SolidTypeSignatureFragment_inputs_definition;
}

export interface SolidTypeSignatureFragment {
  __typename: "Solid";
  outputs: SolidTypeSignatureFragment_outputs[];
  inputs: SolidTypeSignatureFragment_inputs[];
}
