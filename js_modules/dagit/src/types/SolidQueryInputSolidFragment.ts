// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidQueryInputSolidFragment
// ====================================================

export interface SolidQueryInputSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidQueryInputSolidFragment_inputs_dependsOn {
  __typename: "Output";
  solid: SolidQueryInputSolidFragment_inputs_dependsOn_solid;
}

export interface SolidQueryInputSolidFragment_inputs {
  __typename: "Input";
  dependsOn: SolidQueryInputSolidFragment_inputs_dependsOn[];
}

export interface SolidQueryInputSolidFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidQueryInputSolidFragment_outputs_dependedBy {
  __typename: "Input";
  solid: SolidQueryInputSolidFragment_outputs_dependedBy_solid;
}

export interface SolidQueryInputSolidFragment_outputs {
  __typename: "Output";
  dependedBy: SolidQueryInputSolidFragment_outputs_dependedBy[];
}

export interface SolidQueryInputSolidFragment {
  __typename: "Solid";
  name: string;
  inputs: SolidQueryInputSolidFragment_inputs[];
  outputs: SolidQueryInputSolidFragment_outputs[];
}
