// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerParentSolidHandleFragment
// ====================================================

export interface PipelineExplorerParentSolidHandleFragment_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn_definition;
  solid: PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn_solid;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_inputs {
  __typename: "Input";
  definition: PipelineExplorerParentSolidHandleFragment_solid_inputs_definition;
  dependsOn: PipelineExplorerParentSolidHandleFragment_solid_inputs_dependsOn[];
}

export interface PipelineExplorerParentSolidHandleFragment_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy_solid;
  definition: PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy_definition;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_outputs {
  __typename: "Output";
  definition: PipelineExplorerParentSolidHandleFragment_solid_outputs_definition;
  dependedBy: PipelineExplorerParentSolidHandleFragment_solid_outputs_dependedBy[];
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_configField_configType {
  __typename: "CompositeConfigType" | "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_configField_configType;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition_configField | null;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineExplorerParentSolidHandleFragment_solid_definition = PipelineExplorerParentSolidHandleFragment_solid_definition_SolidDefinition | PipelineExplorerParentSolidHandleFragment_solid_definition_CompositeSolidDefinition;

export interface PipelineExplorerParentSolidHandleFragment_solid {
  __typename: "Solid";
  name: string;
  inputs: PipelineExplorerParentSolidHandleFragment_solid_inputs[];
  outputs: PipelineExplorerParentSolidHandleFragment_solid_outputs[];
  definition: PipelineExplorerParentSolidHandleFragment_solid_definition;
}

export interface PipelineExplorerParentSolidHandleFragment {
  __typename: "SolidHandle";
  handleID: string;
  solid: PipelineExplorerParentSolidHandleFragment_solid;
}
