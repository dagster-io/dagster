/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerPipelineFragment
// ====================================================

export interface SidebarTabbedContainerPipelineFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes = SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes = SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_config_configType = SidebarTabbedContainerPipelineFragment_contexts_config_configType_EnumConfigType | SidebarTabbedContainerPipelineFragment_contexts_config_configType_CompositeConfigType;

export interface SidebarTabbedContainerPipelineFragment_contexts_config {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerPipelineFragment_contexts_config_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes = SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes = SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType = SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_EnumConfigType | SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType_CompositeConfigType;

export interface SidebarTabbedContainerPipelineFragment_contexts_resources_config {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerPipelineFragment_contexts_resources_config_configType;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  config: SidebarTabbedContainerPipelineFragment_contexts_resources_config | null;
}

export interface SidebarTabbedContainerPipelineFragment_contexts {
  __typename: "PipelineContext";
  name: string;
  description: string | null;
  config: SidebarTabbedContainerPipelineFragment_contexts_config | null;
  resources: SidebarTabbedContainerPipelineFragment_contexts_resources[];
}

export interface SidebarTabbedContainerPipelineFragment {
  __typename: "Pipeline";
  name: string;
  environmentType: SidebarTabbedContainerPipelineFragment_environmentType;
  description: string | null;
  contexts: SidebarTabbedContainerPipelineFragment_contexts[];
}
