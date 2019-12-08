// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerFragment
// ====================================================

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes = PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes[];
}

export type PipelineExplorerFragment_modes_resources_configField_configType = PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType | PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType;

export interface PipelineExplorerFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_modes_resources_configField_configType;
}

export interface PipelineExplorerFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: PipelineExplorerFragment_modes_resources_configField | null;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes = PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes[];
}

export type PipelineExplorerFragment_modes_loggers_configField_configType = PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType | PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType;

export interface PipelineExplorerFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_modes_loggers_configField_configType;
}

export interface PipelineExplorerFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: PipelineExplorerFragment_modes_loggers_configField | null;
}

export interface PipelineExplorerFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: PipelineExplorerFragment_modes_resources[];
  loggers: PipelineExplorerFragment_modes_loggers[];
}

export interface PipelineExplorerFragment {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  modes: PipelineExplorerFragment_modes[];
}
