/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarPipelineInfoFragment
// ====================================================

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes = SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes = SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_config_configType = SidebarPipelineInfoFragment_contexts_config_configType_EnumConfigType | SidebarPipelineInfoFragment_contexts_config_configType_CompositeConfigType;

export interface SidebarPipelineInfoFragment_contexts_config {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineInfoFragment_contexts_config_configType;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes = SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes = SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_resources_config_configType = SidebarPipelineInfoFragment_contexts_resources_config_configType_EnumConfigType | SidebarPipelineInfoFragment_contexts_resources_config_configType_CompositeConfigType;

export interface SidebarPipelineInfoFragment_contexts_resources_config {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineInfoFragment_contexts_resources_config_configType;
}

export interface SidebarPipelineInfoFragment_contexts_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  config: SidebarPipelineInfoFragment_contexts_resources_config | null;
}

export interface SidebarPipelineInfoFragment_contexts {
  __typename: "PipelineContext";
  name: string;
  description: string | null;
  config: SidebarPipelineInfoFragment_contexts_config | null;
  resources: SidebarPipelineInfoFragment_contexts_resources[];
}

export interface SidebarPipelineInfoFragment {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  contexts: SidebarPipelineInfoFragment_contexts[];
}
