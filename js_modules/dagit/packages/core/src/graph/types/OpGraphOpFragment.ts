/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpGraphOpFragment
// ====================================================

export interface OpGraphOpFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpGraphOpFragment_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpGraphOpFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: OpGraphOpFragment_inputs_dependsOn_definition_type;
}

export interface OpGraphOpFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface OpGraphOpFragment_inputs_dependsOn {
  __typename: "Output";
  definition: OpGraphOpFragment_inputs_dependsOn_definition;
  solid: OpGraphOpFragment_inputs_dependsOn_solid;
}

export interface OpGraphOpFragment_inputs {
  __typename: "Input";
  definition: OpGraphOpFragment_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: OpGraphOpFragment_inputs_dependsOn[];
}

export interface OpGraphOpFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpGraphOpFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface OpGraphOpFragment_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpGraphOpFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: OpGraphOpFragment_outputs_dependedBy_definition_type;
}

export interface OpGraphOpFragment_outputs_dependedBy {
  __typename: "Input";
  solid: OpGraphOpFragment_outputs_dependedBy_solid;
  definition: OpGraphOpFragment_outputs_dependedBy_definition;
}

export interface OpGraphOpFragment_outputs {
  __typename: "Output";
  definition: OpGraphOpFragment_outputs_definition;
  dependedBy: OpGraphOpFragment_outputs_dependedBy[];
}

export interface OpGraphOpFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpGraphOpFragment_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface OpGraphOpFragment_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: OpGraphOpFragment_definition_SolidDefinition_assetNodes_assetKey;
}

export interface OpGraphOpFragment_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpGraphOpFragment_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpGraphOpFragment_definition_SolidDefinition_inputDefinitions_type;
}

export interface OpGraphOpFragment_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpGraphOpFragment_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpGraphOpFragment_definition_SolidDefinition_outputDefinitions_type;
}

export interface OpGraphOpFragment_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface OpGraphOpFragment_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: OpGraphOpFragment_definition_SolidDefinition_configField_configType;
}

export interface OpGraphOpFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: OpGraphOpFragment_definition_SolidDefinition_metadata[];
  assetNodes: OpGraphOpFragment_definition_SolidDefinition_assetNodes[];
  inputDefinitions: OpGraphOpFragment_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: OpGraphOpFragment_definition_SolidDefinition_outputDefinitions[];
  configField: OpGraphOpFragment_definition_SolidDefinition_configField | null;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: OpGraphOpFragment_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface OpGraphOpFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: OpGraphOpFragment_definition_CompositeSolidDefinition_metadata[];
  assetNodes: OpGraphOpFragment_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: OpGraphOpFragment_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: OpGraphOpFragment_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: OpGraphOpFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: OpGraphOpFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type OpGraphOpFragment_definition = OpGraphOpFragment_definition_SolidDefinition | OpGraphOpFragment_definition_CompositeSolidDefinition;

export interface OpGraphOpFragment {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: OpGraphOpFragment_inputs[];
  outputs: OpGraphOpFragment_outputs[];
  definition: OpGraphOpFragment_definition;
}
