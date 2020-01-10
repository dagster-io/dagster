// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarPipelineInfoFragment
// ====================================================

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType = SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType;

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

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType = SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType;

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
