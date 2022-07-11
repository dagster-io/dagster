/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LaunchAssetLoaderResourceQuery
// ====================================================

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType = LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ArrayConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_RegularConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_MapConfigType;

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField {
  __typename: "ConfigTypeField";
  name: string;
  configType: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField_configType;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources_configField | null;
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  id: string;
  resources: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes_resources[];
}

export interface LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  modes: LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline_modes[];
}

export type LaunchAssetLoaderResourceQuery_pipelineOrError = LaunchAssetLoaderResourceQuery_pipelineOrError_PipelineNotFoundError | LaunchAssetLoaderResourceQuery_pipelineOrError_Pipeline;

export interface LaunchAssetLoaderResourceQuery {
  pipelineOrError: LaunchAssetLoaderResourceQuery_pipelineOrError;
}

export interface LaunchAssetLoaderResourceQueryVariables {
  pipelineSelector: PipelineSelector;
}
