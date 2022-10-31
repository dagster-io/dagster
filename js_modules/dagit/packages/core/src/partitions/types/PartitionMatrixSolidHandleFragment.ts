/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PartitionMatrixSolidHandleFragment
// ====================================================

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_configField_configType;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_metadata[];
  assetNodes: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_assetNodes[];
  inputDefinitions: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions[];
  configField: PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition_configField | null;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type PartitionMatrixSolidHandleFragment_solid_definition = PartitionMatrixSolidHandleFragment_solid_definition_SolidDefinition | PartitionMatrixSolidHandleFragment_solid_definition_CompositeSolidDefinition;

export interface PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn_definition_type;
}

export interface PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn {
  __typename: "Output";
  solid: PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn_solid;
  definition: PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn_definition;
}

export interface PartitionMatrixSolidHandleFragment_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_inputs {
  __typename: "Input";
  dependsOn: PartitionMatrixSolidHandleFragment_solid_inputs_dependsOn[];
  definition: PartitionMatrixSolidHandleFragment_solid_inputs_definition;
  isDynamicCollect: boolean;
}

export interface PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy_definition_type;
}

export interface PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy_solid;
  definition: PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy_definition;
}

export interface PartitionMatrixSolidHandleFragment_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PartitionMatrixSolidHandleFragment_solid_outputs {
  __typename: "Output";
  dependedBy: PartitionMatrixSolidHandleFragment_solid_outputs_dependedBy[];
  definition: PartitionMatrixSolidHandleFragment_solid_outputs_definition;
}

export interface PartitionMatrixSolidHandleFragment_solid {
  __typename: "Solid";
  name: string;
  definition: PartitionMatrixSolidHandleFragment_solid_definition;
  inputs: PartitionMatrixSolidHandleFragment_solid_inputs[];
  outputs: PartitionMatrixSolidHandleFragment_solid_outputs[];
  isDynamicMapped: boolean;
}

export interface PartitionMatrixSolidHandleFragment {
  __typename: "SolidHandle";
  handleID: string;
  solid: PartitionMatrixSolidHandleFragment_solid;
}
