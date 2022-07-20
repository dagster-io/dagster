/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphSidebarQuery
// ====================================================

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources[];
  loggers: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PathMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_JsonMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_UrlMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TextMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_FloatMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_IntMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_BoolMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry;

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  modes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes[];
  pipelineSnapshotId: string;
  parentSnapshotId: string | null;
  metadataEntries: AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError";
  message: string;
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetGraphSidebarQuery_pipelineSnapshotOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: AssetGraphSidebarQuery_pipelineSnapshotOrError_PythonError_causes[];
}

export type AssetGraphSidebarQuery_pipelineSnapshotOrError = AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineNotFoundError | AssetGraphSidebarQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | AssetGraphSidebarQuery_pipelineSnapshotOrError_PythonError;

export interface AssetGraphSidebarQuery {
  pipelineSnapshotOrError: AssetGraphSidebarQuery_pipelineSnapshotOrError;
}

export interface AssetGraphSidebarQueryVariables {
  pipelineSelector: PipelineSelector;
}
