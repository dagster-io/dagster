// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigTypeSchemaFragment
// ====================================================

export interface ConfigTypeSchemaFragment_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigTypeSchemaFragment_EnumConfigType {
  __typename: "EnumConfigType";
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigTypeSchemaFragment_RegularConfigType {
  __typename: "RegularConfigType";
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigTypeSchemaFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface ConfigTypeSchemaFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigTypeSchemaFragment_CompositeConfigType_fields[];
}

export interface ConfigTypeSchemaFragment_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type ConfigTypeSchemaFragment = ConfigTypeSchemaFragment_ArrayConfigType | ConfigTypeSchemaFragment_EnumConfigType | ConfigTypeSchemaFragment_RegularConfigType | ConfigTypeSchemaFragment_CompositeConfigType | ConfigTypeSchemaFragment_ScalarUnionConfigType;
