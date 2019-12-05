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

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType_innerTypes[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_innerTypes[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ListConfigType_innerTypes[];
  ofType: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ListConfigType_ofType;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_innerTypes[];
  values: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_values[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_RegularConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ListConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType;

export interface ConfigEditorEnvironmentSchemaFragment {
  __typename: "EnvironmentSchema";
  rootEnvironmentType: ConfigEditorEnvironmentSchemaFragment_rootEnvironmentType;
  allConfigTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes[];
}
