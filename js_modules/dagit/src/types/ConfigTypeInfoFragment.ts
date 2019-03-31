/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigTypeInfoFragment
// ====================================================

export interface ConfigTypeInfoFragment_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeInfoFragment_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeInfoFragment_EnumConfigType_innerTypes[];
}

export interface ConfigTypeInfoFragment_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeInfoFragment_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigTypeInfoFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigTypeInfoFragment_CompositeConfigType_fields_configType;
}

export interface ConfigTypeInfoFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigTypeInfoFragment_CompositeConfigType_innerTypes[];
  fields: ConfigTypeInfoFragment_CompositeConfigType_fields[];
}

export type ConfigTypeInfoFragment = ConfigTypeInfoFragment_EnumConfigType | ConfigTypeInfoFragment_CompositeConfigType;
