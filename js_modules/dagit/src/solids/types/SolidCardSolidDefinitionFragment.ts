// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidCardSolidDefinitionFragment
// ====================================================

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_metadata[];
  inputDefinitions: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: SolidCardSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
  description: string | null;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidCardSolidDefinitionFragment_SolidDefinition_inputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidCardSolidDefinitionFragment_SolidDefinition_outputDefinitions_type;
}

export interface SolidCardSolidDefinitionFragment_SolidDefinition_configField_configType {
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  name: string | null;
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

export type SolidCardSolidDefinitionFragment = SolidCardSolidDefinitionFragment_CompositeSolidDefinition | SolidCardSolidDefinitionFragment_SolidDefinition;
