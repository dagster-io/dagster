// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphSolidFragment
// ====================================================

export interface PipelineGraphSolidFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_inputs_dependsOn_definition_type;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineGraphSolidFragment_inputs_dependsOn_definition;
  solid: PipelineGraphSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineGraphSolidFragment_inputs {
  __typename: "Input";
  definition: PipelineGraphSolidFragment_inputs_definition;
  dependsOn: PipelineGraphSolidFragment_inputs_dependsOn[];
}

export interface PipelineGraphSolidFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_outputs_dependedBy_definition_type;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineGraphSolidFragment_outputs_dependedBy_solid;
  definition: PipelineGraphSolidFragment_outputs_dependedBy_definition;
}

export interface PipelineGraphSolidFragment_outputs {
  __typename: "Output";
  definition: PipelineGraphSolidFragment_outputs_definition;
  dependedBy: PipelineGraphSolidFragment_outputs_dependedBy[];
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineGraphSolidFragment_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineGraphSolidFragment_definition_SolidDefinition_configField_configType;
}

export interface PipelineGraphSolidFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: PipelineGraphSolidFragment_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineGraphSolidFragment_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineGraphSolidFragment_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineGraphSolidFragment_definition_SolidDefinition_configField | null;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineGraphSolidFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineGraphSolidFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineGraphSolidFragment_definition = PipelineGraphSolidFragment_definition_SolidDefinition | PipelineGraphSolidFragment_definition_CompositeSolidDefinition;

export interface PipelineGraphSolidFragment {
  __typename: "Solid";
  name: string;
  inputs: PipelineGraphSolidFragment_inputs[];
  outputs: PipelineGraphSolidFragment_outputs[];
  definition: PipelineGraphSolidFragment_definition;
}
