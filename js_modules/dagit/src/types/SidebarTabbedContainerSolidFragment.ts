// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerSolidFragment
// ====================================================

export interface SidebarTabbedContainerSolidFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  isNothing: boolean;
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_outputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_outputs {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidFragment_outputs_definition;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  isNothing: boolean;
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_inputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition;
  solid: SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid;
}

export interface SidebarTabbedContainerSolidFragment_inputs {
  __typename: "Input";
  definition: SidebarTabbedContainerSolidFragment_inputs_definition;
  dependsOn: SidebarTabbedContainerSolidFragment_inputs_dependsOn[];
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes = SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType = SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  description: string | null;
  metadata: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_metadata[];
  configDefinition: SidebarTabbedContainerSolidFragment_definition_SolidDefinition_configDefinition | null;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  description: string | null;
  metadata: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_metadata[];
  inputMappings: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarTabbedContainerSolidFragment_definition = SidebarTabbedContainerSolidFragment_definition_SolidDefinition | SidebarTabbedContainerSolidFragment_definition_CompositeSolidDefinition;

export interface SidebarTabbedContainerSolidFragment {
  __typename: "Solid";
  outputs: SidebarTabbedContainerSolidFragment_outputs[];
  inputs: SidebarTabbedContainerSolidFragment_inputs[];
  name: string;
  definition: SidebarTabbedContainerSolidFragment_definition;
}
