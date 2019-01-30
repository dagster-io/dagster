/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigTypeSchemaFragment
// ====================================================

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment_EnumConfigType_innerTypes = ConfigTypeSchemaFragment_EnumConfigType_innerTypes_EnumConfigType | ConfigTypeSchemaFragment_EnumConfigType_innerTypes_CompositeConfigType;

export interface ConfigTypeSchemaFragment_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_EnumConfigType_innerTypes[];
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment_CompositeConfigType_innerTypes = ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_EnumConfigType | ConfigTypeSchemaFragment_CompositeConfigType_innerTypes_CompositeConfigType;

export interface ConfigTypeSchemaFragment_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeSchemaFragment_CompositeConfigType_fields_configType;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeSchemaFragment_CompositeConfigType_innerTypes[];
  fields: ConfigTypeSchemaFragment_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment = ConfigTypeSchemaFragment_EnumConfigType | ConfigTypeSchemaFragment_CompositeConfigType;
