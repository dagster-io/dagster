// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeDefinitionFragment
// ====================================================

export interface SolidNodeDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
}

export interface SolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
}

export interface SolidNodeDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: SolidNodeDefinitionFragment_CompositeSolidDefinition_metadata[];
  inputDefinitions: SolidNodeDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: SolidNodeDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
}

export interface SolidNodeDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidNodeDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidNodeDefinitionFragment_SolidDefinition_inputDefinitions_type;
}

export interface SolidNodeDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidNodeDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidNodeDefinitionFragment_SolidDefinition_outputDefinitions_type;
}

export interface SolidNodeDefinitionFragment_SolidDefinition_configField_configType {
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  name: string | null;
  description: string | null;
}

export interface SolidNodeDefinitionFragment_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SolidNodeDefinitionFragment_SolidDefinition_configField_configType;
}

export interface SolidNodeDefinitionFragment_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: SolidNodeDefinitionFragment_SolidDefinition_metadata[];
  inputDefinitions: SolidNodeDefinitionFragment_SolidDefinition_inputDefinitions[];
  outputDefinitions: SolidNodeDefinitionFragment_SolidDefinition_outputDefinitions[];
  configField: SolidNodeDefinitionFragment_SolidDefinition_configField | null;
}

export type SolidNodeDefinitionFragment = SolidNodeDefinitionFragment_CompositeSolidDefinition | SolidNodeDefinitionFragment_SolidDefinition;
