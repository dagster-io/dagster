// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerEnvironmentSchemaFragment
// ====================================================

export interface PipelineExecutionContainerEnvironmentSchemaFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError";
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_rootEnvironmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema {
  __typename: "EnvironmentSchema";
  rootEnvironmentType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_rootEnvironmentType;
  allConfigTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type PipelineExecutionContainerEnvironmentSchemaFragment = PipelineExecutionContainerEnvironmentSchemaFragment_PipelineNotFoundError | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema | PipelineExecutionContainerEnvironmentSchemaFragment_ModeNotFoundError;
