/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphOpFragment
// ====================================================

export interface PipelineGraphOpFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphOpFragment_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphOpFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphOpFragment_inputs_dependsOn_definition_type;
}

export interface PipelineGraphOpFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphOpFragment_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineGraphOpFragment_inputs_dependsOn_definition;
  solid: PipelineGraphOpFragment_inputs_dependsOn_solid;
}

export interface PipelineGraphOpFragment_inputs {
  __typename: "Input";
  definition: PipelineGraphOpFragment_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: PipelineGraphOpFragment_inputs_dependsOn[];
}

export interface PipelineGraphOpFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphOpFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphOpFragment_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphOpFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphOpFragment_outputs_dependedBy_definition_type;
}

export interface PipelineGraphOpFragment_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineGraphOpFragment_outputs_dependedBy_solid;
  definition: PipelineGraphOpFragment_outputs_dependedBy_definition;
}

export interface PipelineGraphOpFragment_outputs {
  __typename: "Output";
  definition: PipelineGraphOpFragment_outputs_definition;
  dependedBy: PipelineGraphOpFragment_outputs_dependedBy[];
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphOpFragment_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineGraphOpFragment_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineGraphOpFragment_definition_SolidDefinition_configField_configType;
}

export interface PipelineGraphOpFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: PipelineGraphOpFragment_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineGraphOpFragment_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineGraphOpFragment_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineGraphOpFragment_definition_SolidDefinition_configField | null;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineGraphOpFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: PipelineGraphOpFragment_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: PipelineGraphOpFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineGraphOpFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineGraphOpFragment_definition = PipelineGraphOpFragment_definition_SolidDefinition | PipelineGraphOpFragment_definition_CompositeSolidDefinition;

export interface PipelineGraphOpFragment {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: PipelineGraphOpFragment_inputs[];
  outputs: PipelineGraphOpFragment_outputs[];
  definition: PipelineGraphOpFragment_definition;
}
