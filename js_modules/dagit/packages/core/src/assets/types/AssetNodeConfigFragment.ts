/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeConfigFragment
// ====================================================

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes = AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeConfigFragment_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeConfigFragment_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes = AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeConfigFragment_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: AssetNodeConfigFragment_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes = AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeConfigFragment_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeConfigFragment_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes = AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeConfigFragment_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeConfigFragment_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes = AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeConfigFragment_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeConfigFragment_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeConfigFragment_configField_configType = AssetNodeConfigFragment_configField_configType_ArrayConfigType | AssetNodeConfigFragment_configField_configType_EnumConfigType | AssetNodeConfigFragment_configField_configType_RegularConfigType | AssetNodeConfigFragment_configField_configType_CompositeConfigType | AssetNodeConfigFragment_configField_configType_ScalarUnionConfigType | AssetNodeConfigFragment_configField_configType_MapConfigType;

export interface AssetNodeConfigFragment_configField {
  __typename: "ConfigTypeField";
  name: string;
  isRequired: boolean;
  configType: AssetNodeConfigFragment_configField_configType;
}

export interface AssetNodeConfigFragment {
  __typename: "AssetNode";
  id: string;
  configField: AssetNodeConfigFragment_configField | null;
}
