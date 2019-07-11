// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeFragment_definition_SolidDefinition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface SolidNodeFragment_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SolidNodeFragment_definition_SolidDefinition_configDefinition_configType;
}

export interface SolidNodeFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: SolidNodeFragment_definition_SolidDefinition_metadata[];
  configDefinition: SolidNodeFragment_definition_SolidDefinition_configDefinition | null;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SolidNodeFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: SolidNodeFragment_definition_CompositeSolidDefinition_metadata[];
  inputMappings: SolidNodeFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SolidNodeFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type SolidNodeFragment_definition = SolidNodeFragment_definition_SolidDefinition | SolidNodeFragment_definition_CompositeSolidDefinition;

export interface SolidNodeFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeFragment_inputs_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
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
  dependsOn: SolidNodeFragment_inputs_dependsOn[];
}

export interface SolidNodeFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeFragment_outputs_definition_type;
}

export interface SolidNodeFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidNodeFragment_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
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
