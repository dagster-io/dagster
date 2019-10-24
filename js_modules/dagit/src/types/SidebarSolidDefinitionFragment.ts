// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidDefinitionFragment
// ====================================================

export interface SidebarSolidDefinitionFragment_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarSolidDefinitionFragment_SolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarSolidDefinitionFragment_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes = SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType = SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_EnumConfigType | SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType_CompositeConfigType;

export interface SidebarSolidDefinitionFragment_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition_configType;
}

export interface SidebarSolidDefinitionFragment_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarSolidDefinitionFragment_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarSolidDefinitionFragment_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarSolidDefinitionFragment_SolidDefinition_metadata[];
  requiredResources: SidebarSolidDefinitionFragment_SolidDefinition_requiredResources[];
  configDefinition: SidebarSolidDefinitionFragment_SolidDefinition_configDefinition | null;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarSolidDefinitionFragment_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarSolidDefinitionFragment_CompositeSolidDefinition_metadata[];
  requiredResources: SidebarSolidDefinitionFragment_CompositeSolidDefinition_requiredResources[];
  inputMappings: SidebarSolidDefinitionFragment_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarSolidDefinitionFragment_CompositeSolidDefinition_outputMappings[];
}

export type SidebarSolidDefinitionFragment = SidebarSolidDefinitionFragment_SolidDefinition | SidebarSolidDefinitionFragment_CompositeSolidDefinition;
