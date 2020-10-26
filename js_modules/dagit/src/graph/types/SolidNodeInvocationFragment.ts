// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeInvocationFragment
// ====================================================

export interface SolidNodeInvocationFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidNodeInvocationFragment_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidNodeInvocationFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeInvocationFragment_inputs_dependsOn_definition_type;
}

export interface SolidNodeInvocationFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeInvocationFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SolidNodeInvocationFragment_inputs_dependsOn_definition;
  solid: SolidNodeInvocationFragment_inputs_dependsOn_solid;
}

export interface SolidNodeInvocationFragment_inputs {
  __typename: "Input";
  definition: SolidNodeInvocationFragment_inputs_definition;
  dependsOn: SolidNodeInvocationFragment_inputs_dependsOn[];
}

export interface SolidNodeInvocationFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidNodeInvocationFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeInvocationFragment_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidNodeInvocationFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeInvocationFragment_outputs_dependedBy_definition_type;
}

export interface SolidNodeInvocationFragment_outputs_dependedBy {
  __typename: "Input";
  solid: SolidNodeInvocationFragment_outputs_dependedBy_solid;
  definition: SolidNodeInvocationFragment_outputs_dependedBy_definition;
}

export interface SolidNodeInvocationFragment_outputs {
  __typename: "Output";
  definition: SolidNodeInvocationFragment_outputs_definition;
  dependedBy: SolidNodeInvocationFragment_outputs_dependedBy[];
}

export interface SolidNodeInvocationFragment {
  __typename: "Solid";
  name: string;
  inputs: SolidNodeInvocationFragment_inputs[];
  outputs: SolidNodeInvocationFragment_outputs[];
}
