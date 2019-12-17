// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphParentSolidFragment
// ====================================================

export interface PipelineGraphParentSolidFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphParentSolidFragment_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphParentSolidFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphParentSolidFragment_inputs_dependsOn_definition_type;
}

export interface PipelineGraphParentSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphParentSolidFragment_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineGraphParentSolidFragment_inputs_dependsOn_definition;
  solid: PipelineGraphParentSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineGraphParentSolidFragment_inputs {
  __typename: "Input";
  definition: PipelineGraphParentSolidFragment_inputs_definition;
  dependsOn: PipelineGraphParentSolidFragment_inputs_dependsOn[];
}

export interface PipelineGraphParentSolidFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphParentSolidFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphParentSolidFragment_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphParentSolidFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphParentSolidFragment_outputs_dependedBy_definition_type;
}

export interface PipelineGraphParentSolidFragment_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineGraphParentSolidFragment_outputs_dependedBy_solid;
  definition: PipelineGraphParentSolidFragment_outputs_dependedBy_definition;
}

export interface PipelineGraphParentSolidFragment_outputs {
  __typename: "Output";
  definition: PipelineGraphParentSolidFragment_outputs_definition;
  dependedBy: PipelineGraphParentSolidFragment_outputs_dependedBy[];
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphParentSolidFragment_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphParentSolidFragment_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_configField_configType {
  __typename: "CompositeConfigType" | "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineGraphParentSolidFragment_definition_SolidDefinition_configField_configType;
}

export interface PipelineGraphParentSolidFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: PipelineGraphParentSolidFragment_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineGraphParentSolidFragment_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineGraphParentSolidFragment_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineGraphParentSolidFragment_definition_SolidDefinition_configField | null;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineGraphParentSolidFragment_definition = PipelineGraphParentSolidFragment_definition_SolidDefinition | PipelineGraphParentSolidFragment_definition_CompositeSolidDefinition;

export interface PipelineGraphParentSolidFragment {
  __typename: "Solid";
  name: string;
  inputs: PipelineGraphParentSolidFragment_inputs[];
  outputs: PipelineGraphParentSolidFragment_outputs[];
  definition: PipelineGraphParentSolidFragment_definition;
}
