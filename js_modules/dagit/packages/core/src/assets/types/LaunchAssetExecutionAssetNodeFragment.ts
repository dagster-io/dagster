/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchAssetExecutionAssetNodeFragment
// ====================================================

export interface LaunchAssetExecutionAssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_dependencyKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: LaunchAssetExecutionAssetNodeFragment_repository_location;
}

export interface LaunchAssetExecutionAssetNodeFragment_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes = LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes = LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes = LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes = LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes = LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type LaunchAssetExecutionAssetNodeFragment_configField_configType = LaunchAssetExecutionAssetNodeFragment_configField_configType_ArrayConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_EnumConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_RegularConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_CompositeConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_ScalarUnionConfigType | LaunchAssetExecutionAssetNodeFragment_configField_configType_MapConfigType;

export interface LaunchAssetExecutionAssetNodeFragment_configField {
  __typename: "ConfigTypeField";
  name: string;
  isRequired: boolean;
  configType: LaunchAssetExecutionAssetNodeFragment_configField_configType;
}

export interface LaunchAssetExecutionAssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  jobNames: string[];
  graphName: string | null;
  partitionDefinition: string | null;
  assetKey: LaunchAssetExecutionAssetNodeFragment_assetKey;
  dependencyKeys: LaunchAssetExecutionAssetNodeFragment_dependencyKeys[];
  repository: LaunchAssetExecutionAssetNodeFragment_repository;
  requiredResources: LaunchAssetExecutionAssetNodeFragment_requiredResources[];
  configField: LaunchAssetExecutionAssetNodeFragment_configField | null;
}
