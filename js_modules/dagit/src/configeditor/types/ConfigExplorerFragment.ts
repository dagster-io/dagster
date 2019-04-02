/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigExplorerFragment
// ====================================================

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes = ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType | ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigExplorerFragment_contexts_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_configType_EnumConfigType_innerTypes[];
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes = ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType | ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_fields_configType;
}

export interface ConfigExplorerFragment_contexts_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_innerTypes[];
  fields: ConfigExplorerFragment_contexts_config_configType_CompositeConfigType_fields[];
}

export type ConfigExplorerFragment_contexts_config_configType = ConfigExplorerFragment_contexts_config_configType_EnumConfigType | ConfigExplorerFragment_contexts_config_configType_CompositeConfigType;

export interface ConfigExplorerFragment_contexts_config {
  __typename: "ConfigTypeField";
  configType: ConfigExplorerFragment_contexts_config_configType;
}

export interface ConfigExplorerFragment_contexts {
  __typename: "PipelineContext";
  name: string;
  description: string | null;
  config: ConfigExplorerFragment_contexts_config | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes = ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes = ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_configType = ConfigExplorerFragment_solids_definition_configDefinition_configType_EnumConfigType | ConfigExplorerFragment_solids_definition_configDefinition_configType_CompositeConfigType;

export interface ConfigExplorerFragment_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: ConfigExplorerFragment_solids_definition_configDefinition_configType;
}

export interface ConfigExplorerFragment_solids_definition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  configDefinition: ConfigExplorerFragment_solids_definition_configDefinition | null;
}

export interface ConfigExplorerFragment_solids {
  __typename: "Solid";
  definition: ConfigExplorerFragment_solids_definition;
}

export interface ConfigExplorerFragment {
  __typename: "Pipeline";
  contexts: ConfigExplorerFragment_contexts[];
  solids: ConfigExplorerFragment_solids[];
}
