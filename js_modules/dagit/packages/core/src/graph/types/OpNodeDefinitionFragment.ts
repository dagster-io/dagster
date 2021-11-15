// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpNodeDefinitionFragment
// ====================================================

export interface OpNodeDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpNodeDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpNodeDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpNodeDefinitionFragment_SolidDefinition_inputDefinitions_type;
}

export interface OpNodeDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpNodeDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpNodeDefinitionFragment_SolidDefinition_outputDefinitions_type;
}

export interface OpNodeDefinitionFragment_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface OpNodeDefinitionFragment_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: OpNodeDefinitionFragment_SolidDefinition_configField_configType;
}

export interface OpNodeDefinitionFragment_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: OpNodeDefinitionFragment_SolidDefinition_metadata[];
  inputDefinitions: OpNodeDefinitionFragment_SolidDefinition_inputDefinitions[];
  outputDefinitions: OpNodeDefinitionFragment_SolidDefinition_outputDefinitions[];
  configField: OpNodeDefinitionFragment_SolidDefinition_configField | null;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface OpNodeDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: OpNodeDefinitionFragment_CompositeSolidDefinition_metadata[];
  inputDefinitions: OpNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: OpNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: OpNodeDefinitionFragment_CompositeSolidDefinition_inputMappings[];
  outputMappings: OpNodeDefinitionFragment_CompositeSolidDefinition_outputMappings[];
}

export type OpNodeDefinitionFragment = OpNodeDefinitionFragment_SolidDefinition | OpNodeDefinitionFragment_CompositeSolidDefinition;
