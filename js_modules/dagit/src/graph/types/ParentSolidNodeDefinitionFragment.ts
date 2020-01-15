// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ParentSolidNodeDefinitionFragment
// ====================================================

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: ParentSolidNodeDefinitionFragment_SolidDefinition_inputDefinitions_type;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: ParentSolidNodeDefinitionFragment_SolidDefinition_outputDefinitions_type;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_configField_configType {
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: ParentSolidNodeDefinitionFragment_SolidDefinition_configField_configType;
}

export interface ParentSolidNodeDefinitionFragment_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: ParentSolidNodeDefinitionFragment_SolidDefinition_metadata[];
  inputDefinitions: ParentSolidNodeDefinitionFragment_SolidDefinition_inputDefinitions[];
  outputDefinitions: ParentSolidNodeDefinitionFragment_SolidDefinition_outputDefinitions[];
  configField: ParentSolidNodeDefinitionFragment_SolidDefinition_configField | null;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface ParentSolidNodeDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_metadata[];
  inputDefinitions: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_inputMappings[];
  outputMappings: ParentSolidNodeDefinitionFragment_CompositeSolidDefinition_outputMappings[];
}

export type ParentSolidNodeDefinitionFragment = ParentSolidNodeDefinitionFragment_SolidDefinition | ParentSolidNodeDefinitionFragment_CompositeSolidDefinition;
