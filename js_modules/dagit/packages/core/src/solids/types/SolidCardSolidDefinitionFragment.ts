// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidCardSolidDefinitionFragment
// ====================================================

export interface SolidCardSolidDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SolidCardSolidDefinitionFragment_SolidDefinition_configField_configType;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: SolidCardSolidDefinitionFragment_SolidDefinition_metadata[];
  inputDefinitions: SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions[];
  outputDefinitions: SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions[];
  configField: SolidCardSolidDefinitionFragment_SolidDefinition_configField | null;
  description: string | null;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_metadata[];
  inputDefinitions: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputMappings[];
  outputMappings: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputMappings[];
  description: string | null;
}

export type SolidCardSolidDefinitionFragment = SolidCardSolidDefinitionFragment_SolidDefinition | SolidCardSolidDefinitionFragment_CompositeSolidDefinition;
