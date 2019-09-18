// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerFragment
// ====================================================

export interface PipelineExecutionContainerFragment_PythonError {
  __typename: "PythonError" | "PipelineNotFoundError";
}

export interface PipelineExecutionContainerFragment_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_Pipeline_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_values[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType = PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_fields[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType_innerTypes[];
}

export type PipelineExecutionContainerFragment_Pipeline_configTypes = PipelineExecutionContainerFragment_Pipeline_configTypes_RegularConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_EnumConfigType | PipelineExecutionContainerFragment_Pipeline_configTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_Pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionContainerFragment_Pipeline_modes[];
  environmentType: PipelineExecutionContainerFragment_Pipeline_environmentType;
  configTypes: PipelineExecutionContainerFragment_Pipeline_configTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_values[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_CompositeConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_fields[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType_innerTypes[];
}

export type PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes = PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_RegularConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_EnumConfigType | PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment_InvalidSubsetError_pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_modes[];
  environmentType: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_environmentType;
  configTypes: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline_configTypes[];
}

export interface PipelineExecutionContainerFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
  pipeline: PipelineExecutionContainerFragment_InvalidSubsetError_pipeline;
}

export type PipelineExecutionContainerFragment = PipelineExecutionContainerFragment_PythonError | PipelineExecutionContainerFragment_Pipeline | PipelineExecutionContainerFragment_InvalidSubsetError;
