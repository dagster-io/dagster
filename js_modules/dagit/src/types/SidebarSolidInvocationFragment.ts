// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInvocationFragment
// ====================================================

export interface SidebarSolidInvocationFragment_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidInvocationFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarSolidInvocationFragment_inputs_definition_type;
}

export interface SidebarSolidInvocationFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidInvocationFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInvocationFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarSolidInvocationFragment_inputs_dependsOn_definition;
  solid: SidebarSolidInvocationFragment_inputs_dependsOn_solid;
}

export interface SidebarSolidInvocationFragment_inputs {
  __typename: "Input";
  definition: SidebarSolidInvocationFragment_inputs_definition;
  dependsOn: SidebarSolidInvocationFragment_inputs_dependsOn[];
}

export interface SidebarSolidInvocationFragment_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidInvocationFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  type: SidebarSolidInvocationFragment_outputs_definition_type;
}

export interface SidebarSolidInvocationFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidInvocationFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInvocationFragment_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarSolidInvocationFragment_outputs_dependedBy_definition;
  solid: SidebarSolidInvocationFragment_outputs_dependedBy_solid;
}

export interface SidebarSolidInvocationFragment_outputs {
  __typename: "Output";
  definition: SidebarSolidInvocationFragment_outputs_definition;
  dependedBy: SidebarSolidInvocationFragment_outputs_dependedBy[];
}

export interface SidebarSolidInvocationFragment {
  __typename: "Solid";
  name: string;
  inputs: SidebarSolidInvocationFragment_inputs[];
  outputs: SidebarSolidInvocationFragment_outputs[];
}
