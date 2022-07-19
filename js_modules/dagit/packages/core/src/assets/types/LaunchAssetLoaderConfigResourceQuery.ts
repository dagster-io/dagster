/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LaunchAssetLoaderConfigResourceQuery
// ====================================================

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType;

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField {
  __typename: "ConfigTypeField";
  name: string;
  isRequired: boolean;
  configType: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources_configField | null;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  id: string;
  resources: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes_resources[];
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_presets {
  __typename: "PipelinePreset";
  runConfigYaml: string;
}

export interface LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  modes: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_modes[];
  presets: LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline_presets[];
}

export type LaunchAssetLoaderConfigResourceQuery_pipelineOrError = LaunchAssetLoaderConfigResourceQuery_pipelineOrError_PipelineNotFoundError | LaunchAssetLoaderConfigResourceQuery_pipelineOrError_Pipeline;

export interface LaunchAssetLoaderConfigResourceQuery {
  pipelineOrError: LaunchAssetLoaderConfigResourceQuery_pipelineOrError;
}

export interface LaunchAssetLoaderConfigResourceQueryVariables {
  pipelineSelector: PipelineSelector;
}
