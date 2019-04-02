/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerFragment
// ====================================================

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes = PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_contexts_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes = PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_contexts_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_contexts_config_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_contexts_config_configType = PipelineExplorerFragment_contexts_config_configType_EnumConfigType | PipelineExplorerFragment_contexts_config_configType_CompositeConfigType;

export interface PipelineExplorerFragment_contexts_config {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_contexts_config_configType;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes = PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes = PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_contexts_resources_config_configType = PipelineExplorerFragment_contexts_resources_config_configType_EnumConfigType | PipelineExplorerFragment_contexts_resources_config_configType_CompositeConfigType;

export interface PipelineExplorerFragment_contexts_resources_config {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_contexts_resources_config_configType;
}

export interface PipelineExplorerFragment_contexts_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  config: PipelineExplorerFragment_contexts_resources_config | null;
}

export interface PipelineExplorerFragment_contexts {
  __typename: "PipelineContext";
  name: string;
  description: string | null;
  config: PipelineExplorerFragment_contexts_config | null;
  resources: PipelineExplorerFragment_contexts_resources[];
}

export interface PipelineExplorerFragment_solids_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_solids_definition_configDefinition_configType;
}

export interface PipelineExplorerFragment_solids_definition {
  __typename: "SolidDefinition";
  metadata: PipelineExplorerFragment_solids_definition_metadata[];
  configDefinition: PipelineExplorerFragment_solids_definition_configDefinition | null;
}

export interface PipelineExplorerFragment_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineExplorerFragment_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerFragment_solids_inputs_definition_type;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerFragment_solids_inputs_dependsOn_definition;
  solid: PipelineExplorerFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineExplorerFragment_solids_inputs {
  __typename: "Input";
  definition: PipelineExplorerFragment_solids_inputs_definition;
  dependsOn: PipelineExplorerFragment_solids_inputs_dependsOn | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerFragment_solids_outputs_definition_type;
  expectations: PipelineExplorerFragment_solids_outputs_definition_expectations[];
}

export interface PipelineExplorerFragment_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerFragment_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerFragment_solids_outputs_dependedBy_solid;
}

export interface PipelineExplorerFragment_solids_outputs {
  __typename: "Output";
  definition: PipelineExplorerFragment_solids_outputs_definition;
  dependedBy: PipelineExplorerFragment_solids_outputs_dependedBy[];
}

export interface PipelineExplorerFragment_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineExplorerFragment_solids_definition;
  inputs: PipelineExplorerFragment_solids_inputs[];
  outputs: PipelineExplorerFragment_solids_outputs[];
}

export interface PipelineExplorerFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
}

export interface PipelineExplorerFragment {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  contexts: PipelineExplorerFragment_contexts[];
  solids: PipelineExplorerFragment_solids[];
  environmentType: PipelineExplorerFragment_environmentType;
}
