// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarOpInvocationFragment
// ====================================================

export interface SidebarOpInvocationFragment_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpInvocationFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarOpInvocationFragment_inputs_definition_type;
}

export interface SidebarOpInvocationFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarOpInvocationFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarOpInvocationFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarOpInvocationFragment_inputs_dependsOn_definition;
  solid: SidebarOpInvocationFragment_inputs_dependsOn_solid;
}

export interface SidebarOpInvocationFragment_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarOpInvocationFragment_inputs_definition;
  dependsOn: SidebarOpInvocationFragment_inputs_dependsOn[];
}

export interface SidebarOpInvocationFragment_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpInvocationFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarOpInvocationFragment_outputs_definition_type;
}

export interface SidebarOpInvocationFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarOpInvocationFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarOpInvocationFragment_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarOpInvocationFragment_outputs_dependedBy_definition;
  solid: SidebarOpInvocationFragment_outputs_dependedBy_solid;
}

export interface SidebarOpInvocationFragment_outputs {
  __typename: "Output";
  definition: SidebarOpInvocationFragment_outputs_definition;
  dependedBy: SidebarOpInvocationFragment_outputs_dependedBy[];
}

export interface SidebarOpInvocationFragment {
  __typename: "Solid";
  name: string;
  inputs: SidebarOpInvocationFragment_inputs[];
  outputs: SidebarOpInvocationFragment_outputs[];
}
