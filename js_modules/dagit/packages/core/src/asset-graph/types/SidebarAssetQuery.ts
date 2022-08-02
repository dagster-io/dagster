/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarAssetQuery
// ====================================================

export interface SidebarAssetQuery_assetNodeOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType = SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_configField {
  __typename: "ConfigTypeField";
  name: string;
  isRequired: boolean;
  configType: SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table_schema;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry_table;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries = SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_PathMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_JsonMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_UrlMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TextMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_MarkdownMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_PythonArtifactMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_FloatMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_IntMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_BoolMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_PipelineRunMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_AssetMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries_TableSchemaMetadataEntry;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table_schema;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry_table;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_PathMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_JsonMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_UrlMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TextMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_MarkdownMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_PythonArtifactMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_FloatMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_IntMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_BoolMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_PipelineRunMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_AssetMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries_TableSchemaMetadataEntry;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table_schema;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry_table;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_PathMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_JsonMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_UrlMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TextMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_MarkdownMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_PythonArtifactMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_FloatMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_IntMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_BoolMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_PipelineRunMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_AssetMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableMetadataEntry | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries_TableSchemaMetadataEntry;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType = SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType | SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType;

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_metadataEntries[];
  inputSchemaType: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_inputSchemaType | null;
  outputSchemaType: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes_outputSchemaType | null;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_metadataEntries[];
  inputSchemaType: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_inputSchemaType | null;
  outputSchemaType: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_outputSchemaType | null;
  innerTypes: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type_innerTypes[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions {
  __typename: "OutputDefinition";
  type: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions_type;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_op {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: SidebarAssetQuery_assetNodeOrError_AssetNode_op_metadata[];
  outputDefinitions: SidebarAssetQuery_assetNodeOrError_AssetNode_op_outputDefinitions[];
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: SidebarAssetQuery_assetNodeOrError_AssetNode_repository_location;
}

export interface SidebarAssetQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  description: string | null;
  configField: SidebarAssetQuery_assetNodeOrError_AssetNode_configField | null;
  metadataEntries: SidebarAssetQuery_assetNodeOrError_AssetNode_metadataEntries[];
  partitionDefinition: string | null;
  assetKey: SidebarAssetQuery_assetNodeOrError_AssetNode_assetKey;
  op: SidebarAssetQuery_assetNodeOrError_AssetNode_op | null;
  repository: SidebarAssetQuery_assetNodeOrError_AssetNode_repository;
}

export type SidebarAssetQuery_assetNodeOrError = SidebarAssetQuery_assetNodeOrError_AssetNotFoundError | SidebarAssetQuery_assetNodeOrError_AssetNode;

export interface SidebarAssetQuery {
  assetNodeOrError: SidebarAssetQuery_assetNodeOrError;
}

export interface SidebarAssetQueryVariables {
  assetKey: AssetKeyInput;
}
