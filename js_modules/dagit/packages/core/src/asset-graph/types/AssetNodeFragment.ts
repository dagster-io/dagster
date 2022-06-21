/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeFragment
// ====================================================

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes = AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes = AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: AssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes = AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes = AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes = AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeFragment_configField_configType = AssetNodeFragment_configField_configType_ArrayConfigType | AssetNodeFragment_configField_configType_EnumConfigType | AssetNodeFragment_configField_configType_RegularConfigType | AssetNodeFragment_configField_configType_CompositeConfigType | AssetNodeFragment_configField_configType_ScalarUnionConfigType | AssetNodeFragment_configField_configType_MapConfigType;

export interface AssetNodeFragment_configField {
  __typename: "ConfigTypeField";
  name: string;
  configType: AssetNodeFragment_configField_configType;
}

export interface AssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeFragment_repository_location;
}

export interface AssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  configField: AssetNodeFragment_configField | null;
  graphName: string | null;
  jobNames: string[];
  opNames: string[];
  description: string | null;
  partitionDefinition: string | null;
  computeKind: string | null;
  assetKey: AssetNodeFragment_assetKey;
  repository: AssetNodeFragment_repository;
}
