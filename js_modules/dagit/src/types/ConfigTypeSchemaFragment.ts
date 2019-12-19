// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigTypeSchemaFragment
// ====================================================

export interface ConfigTypeSchemaFragment_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigTypeSchemaFragment_CompositeConfigType_fields[];
}

export type ConfigTypeSchemaFragment = ConfigTypeSchemaFragment_EnumConfigType | ConfigTypeSchemaFragment_CompositeConfigType;
