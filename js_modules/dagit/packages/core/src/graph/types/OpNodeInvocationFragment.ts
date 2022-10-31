/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpNodeInvocationFragment
// ====================================================

export interface OpNodeInvocationFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpNodeInvocationFragment_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpNodeInvocationFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: OpNodeInvocationFragment_inputs_dependsOn_definition_type;
}

export interface OpNodeInvocationFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface OpNodeInvocationFragment_inputs_dependsOn {
  __typename: "Output";
  definition: OpNodeInvocationFragment_inputs_dependsOn_definition;
  solid: OpNodeInvocationFragment_inputs_dependsOn_solid;
}

export interface OpNodeInvocationFragment_inputs {
  __typename: "Input";
  definition: OpNodeInvocationFragment_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: OpNodeInvocationFragment_inputs_dependsOn[];
}

export interface OpNodeInvocationFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpNodeInvocationFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface OpNodeInvocationFragment_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpNodeInvocationFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: OpNodeInvocationFragment_outputs_dependedBy_definition_type;
}

export interface OpNodeInvocationFragment_outputs_dependedBy {
  __typename: "Input";
  solid: OpNodeInvocationFragment_outputs_dependedBy_solid;
  definition: OpNodeInvocationFragment_outputs_dependedBy_definition;
}

export interface OpNodeInvocationFragment_outputs {
  __typename: "Output";
  definition: OpNodeInvocationFragment_outputs_definition;
  dependedBy: OpNodeInvocationFragment_outputs_dependedBy[];
}

export interface OpNodeInvocationFragment {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: OpNodeInvocationFragment_inputs[];
  outputs: OpNodeInvocationFragment_outputs[];
}
