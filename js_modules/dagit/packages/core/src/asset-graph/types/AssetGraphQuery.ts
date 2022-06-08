/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, AssetGroupSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphQuery
// ====================================================

export interface AssetGraphQuery_assetNodes_dependencyKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_dependedByKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphQuery_assetNodes_configField_configType = AssetGraphQuery_assetNodes_configField_configType_ArrayConfigType | AssetGraphQuery_assetNodes_configField_configType_EnumConfigType | AssetGraphQuery_assetNodes_configField_configType_RegularConfigType | AssetGraphQuery_assetNodes_configField_configType_CompositeConfigType | AssetGraphQuery_assetNodes_configField_configType_ScalarUnionConfigType | AssetGraphQuery_assetNodes_configField_configType_MapConfigType;

export interface AssetGraphQuery_assetNodes_configField {
  __typename: "ConfigTypeField";
  name: string;
  configType: AssetGraphQuery_assetNodes_configField_configType;
}

export interface AssetGraphQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetGraphQuery_assetNodes_repository_location;
}

export interface AssetGraphQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  dependencyKeys: AssetGraphQuery_assetNodes_dependencyKeys[];
  dependedByKeys: AssetGraphQuery_assetNodes_dependedByKeys[];
  configField: AssetGraphQuery_assetNodes_configField | null;
  graphName: string | null;
  jobNames: string[];
  opNames: string[];
  description: string | null;
  partitionDefinition: string | null;
  computeKind: string | null;
  assetKey: AssetGraphQuery_assetNodes_assetKey;
  repository: AssetGraphQuery_assetNodes_repository;
}

export interface AssetGraphQuery {
  assetNodes: AssetGraphQuery_assetNodes[];
}

export interface AssetGraphQueryVariables {
  pipelineSelector?: PipelineSelector | null;
  groupSelector?: AssetGroupSelector | null;
}
