/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LaunchAssetLoaderQuery
// ====================================================

export interface LaunchAssetLoaderQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_dependencyKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: LaunchAssetLoaderQuery_assetNodes_repository_location;
}

export interface LaunchAssetLoaderQuery_assetNodes_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes = LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes = LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes = LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes = LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes = LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type LaunchAssetLoaderQuery_assetNodes_configField_configType = LaunchAssetLoaderQuery_assetNodes_configField_configType_ArrayConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_EnumConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_RegularConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_CompositeConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_ScalarUnionConfigType | LaunchAssetLoaderQuery_assetNodes_configField_configType_MapConfigType;

export interface LaunchAssetLoaderQuery_assetNodes_configField {
  __typename: "ConfigTypeField";
  name: string;
  isRequired: boolean;
  configType: LaunchAssetLoaderQuery_assetNodes_configField_configType;
}

export interface LaunchAssetLoaderQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  jobNames: string[];
  graphName: string | null;
  partitionDefinition: string | null;
  assetKey: LaunchAssetLoaderQuery_assetNodes_assetKey;
  dependencyKeys: LaunchAssetLoaderQuery_assetNodes_dependencyKeys[];
  repository: LaunchAssetLoaderQuery_assetNodes_repository;
  requiredResources: LaunchAssetLoaderQuery_assetNodes_requiredResources[];
  configField: LaunchAssetLoaderQuery_assetNodes_configField | null;
}

export interface LaunchAssetLoaderQuery {
  assetNodes: LaunchAssetLoaderQuery_assetNodes[];
}

export interface LaunchAssetLoaderQueryVariables {
  assetKeys: AssetKeyInput[];
}
