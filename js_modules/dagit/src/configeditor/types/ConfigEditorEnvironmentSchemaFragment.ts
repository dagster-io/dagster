// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorEnvironmentSchemaFragment
// ====================================================

export interface ConfigEditorEnvironmentSchemaFragment_rootEnvironmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_values[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType_fields[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType_fields[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_innerTypes[];
  ofType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_CompositeConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  description: string | null;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_CompositeConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields[];
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment {
  __typename: "EnvironmentSchema";
  rootEnvironmentType: ConfigEditorEnvironmentSchemaFragment_rootEnvironmentType;
  allConfigTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes[];
}
