// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: OpCardSolidDefinitionFragment
// ====================================================

export interface OpCardSolidDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpCardSolidDefinitionFragment_SolidDefinition_inputDefinitions_type;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpCardSolidDefinitionFragment_SolidDefinition_outputDefinitions_type;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: OpCardSolidDefinitionFragment_SolidDefinition_configField_configType;
}

export interface OpCardSolidDefinitionFragment_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: OpCardSolidDefinitionFragment_SolidDefinition_metadata[];
  inputDefinitions: OpCardSolidDefinitionFragment_SolidDefinition_inputDefinitions[];
  outputDefinitions: OpCardSolidDefinitionFragment_SolidDefinition_outputDefinitions[];
  configField: OpCardSolidDefinitionFragment_SolidDefinition_configField | null;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface OpCardSolidDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: OpCardSolidDefinitionFragment_CompositeSolidDefinition_metadata[];
  inputDefinitions: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: OpCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings[];
  outputMappings: OpCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings[];
}

export type OpCardSolidDefinitionFragment = OpCardSolidDefinitionFragment_SolidDefinition | OpCardSolidDefinitionFragment_CompositeSolidDefinition;
