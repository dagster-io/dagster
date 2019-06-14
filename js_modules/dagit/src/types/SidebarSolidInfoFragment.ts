// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInfoFragment
// ====================================================

export interface SidebarSolidInfoFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarSolidInfoFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_outputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInfoFragment_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarSolidInfoFragment_outputs_dependedBy_definition;
  solid: SidebarSolidInfoFragment_outputs_dependedBy_solid;
}

export interface SidebarSolidInfoFragment_outputs {
  __typename: "Output";
  definition: SidebarSolidInfoFragment_outputs_definition;
  dependedBy: SidebarSolidInfoFragment_outputs_dependedBy[];
}

export interface SidebarSolidInfoFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SidebarSolidInfoFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_inputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarSolidInfoFragment_inputs_dependsOn_definition;
  solid: SidebarSolidInfoFragment_inputs_dependsOn_solid;
}

export interface SidebarSolidInfoFragment_inputs {
  __typename: "Input";
  definition: SidebarSolidInfoFragment_inputs_definition;
  dependsOn: SidebarSolidInfoFragment_inputs_dependsOn[];
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes = SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType = SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_EnumConfigType | SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition_configType;
}

export interface SidebarSolidInfoFragment_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: SidebarSolidInfoFragment_definition_SolidDefinition_metadata[];
  configDefinition: SidebarSolidInfoFragment_definition_SolidDefinition_configDefinition | null;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarSolidInfoFragment_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_metadata[];
  inputMappings: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarSolidInfoFragment_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarSolidInfoFragment_definition = SidebarSolidInfoFragment_definition_SolidDefinition | SidebarSolidInfoFragment_definition_CompositeSolidDefinition;

export interface SidebarSolidInfoFragment {
  __typename: "Solid";
  outputs: SidebarSolidInfoFragment_outputs[];
  inputs: SidebarSolidInfoFragment_inputs[];
  name: string;
  definition: SidebarSolidInfoFragment_definition;
}
