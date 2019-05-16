// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarPipelineInfoFragment
// ====================================================

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType = SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineInfoFragment_modes_resources_configField_configType;
}

export interface SidebarPipelineInfoFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarPipelineInfoFragment_modes_resources_configField | null;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields_configType;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType = SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineInfoFragment_modes_loggers_configField_configType;
}

export interface SidebarPipelineInfoFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarPipelineInfoFragment_modes_loggers_configField | null;
}

export interface SidebarPipelineInfoFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: SidebarPipelineInfoFragment_modes_resources[];
  loggers: SidebarPipelineInfoFragment_modes_loggers[];
}

export interface SidebarPipelineInfoFragment {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  modes: SidebarPipelineInfoFragment_modes[];
}
