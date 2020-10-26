// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type TypeExplorerFragment_inputSchemaType = TypeExplorerFragment_inputSchemaType_ArrayConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType;

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type TypeExplorerFragment_outputSchemaType = TypeExplorerFragment_outputSchemaType_ArrayConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType;

export interface TypeExplorerFragment {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerFragment_inputSchemaType | null;
  outputSchemaType: TypeExplorerFragment_outputSchemaType | null;
}
