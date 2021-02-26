// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerSolidHandleFragment
// ====================================================

export interface PipelineExplorerSolidHandleFragment_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn_definition;
  solid: PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn_solid;
}

export interface PipelineExplorerSolidHandleFragment_solid_inputs {
  __typename: "Input";
  definition: PipelineExplorerSolidHandleFragment_solid_inputs_definition;
  dependsOn: PipelineExplorerSolidHandleFragment_solid_inputs_dependsOn[];
}

export interface PipelineExplorerSolidHandleFragment_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy_solid;
  definition: PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy_definition;
}

export interface PipelineExplorerSolidHandleFragment_solid_outputs {
  __typename: "Output";
  definition: PipelineExplorerSolidHandleFragment_solid_outputs_definition;
  dependedBy: PipelineExplorerSolidHandleFragment_solid_outputs_dependedBy[];
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField_configType;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField | null;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineExplorerSolidHandleFragment_solid_definition = PipelineExplorerSolidHandleFragment_solid_definition_SolidDefinition | PipelineExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition;

export interface PipelineExplorerSolidHandleFragment_solid {
  __typename: "Solid";
  name: string;
  inputs: PipelineExplorerSolidHandleFragment_solid_inputs[];
  outputs: PipelineExplorerSolidHandleFragment_solid_outputs[];
  definition: PipelineExplorerSolidHandleFragment_solid_definition;
}

export interface PipelineExplorerSolidHandleFragment {
  __typename: "SolidHandle";
  handleID: string;
  solid: PipelineExplorerSolidHandleFragment_solid;
}
