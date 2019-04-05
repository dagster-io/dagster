/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeFragment_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface SolidNodeFragment_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SolidNodeFragment_definition_configDefinition_configType;
}

export interface SolidNodeFragment_definition {
  __typename: "SolidDefinition";
  metadata: SolidNodeFragment_definition_metadata[];
  configDefinition: SolidNodeFragment_definition_configDefinition | null;
}

export interface SolidNodeFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface SolidNodeFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeFragment_inputs_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface SolidNodeFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeFragment_inputs_dependsOn_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SolidNodeFragment_inputs_dependsOn_definition;
  solid: SolidNodeFragment_inputs_dependsOn_solid;
}

export interface SolidNodeFragment_inputs {
  __typename: "Input";
  definition: SolidNodeFragment_inputs_definition;
  dependsOn: SolidNodeFragment_inputs_dependsOn | null;
}

export interface SolidNodeFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface SolidNodeFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeFragment_outputs_definition_type;
  expectations: SolidNodeFragment_outputs_definition_expectations[];
}

export interface SolidNodeFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface SolidNodeFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeFragment_outputs_dependedBy_definition_type;
}

export interface SolidNodeFragment_outputs_dependedBy {
  __typename: "Input";
  solid: SolidNodeFragment_outputs_dependedBy_solid;
  definition: SolidNodeFragment_outputs_dependedBy_definition;
}

export interface SolidNodeFragment_outputs {
  __typename: "Output";
  definition: SolidNodeFragment_outputs_definition;
  dependedBy: SolidNodeFragment_outputs_dependedBy[];
}

export interface SolidNodeFragment {
  __typename: "Solid";
  name: string;
  definition: SolidNodeFragment_definition;
  inputs: SolidNodeFragment_inputs[];
  outputs: SolidNodeFragment_outputs[];
}
