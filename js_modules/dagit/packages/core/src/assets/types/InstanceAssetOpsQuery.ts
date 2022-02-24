/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: InstanceAssetOpsQuery
// ====================================================

export interface InstanceAssetOpsQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField_configType;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources_configField | null;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ArrayConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_EnumConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_RegularConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_CompositeConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_ScalarUnionConfigType | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType_MapConfigType;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField_configType;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers_configField | null;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_resources[];
  loggers: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes_loggers[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  assetKey: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_configField_configType;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  assetNodes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_assetNodes[];
  name: string;
  description: string | null;
  metadata: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_metadata[];
  inputDefinitions: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_outputDefinitions[];
  configField: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition_configField | null;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  assetKey: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  assetNodes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes[];
  name: string;
  description: string | null;
  metadata: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition = InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_SolidDefinition | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition_CompositeSolidDefinition;

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn_definition;
  solid: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn_solid;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs {
  __typename: "Input";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs_dependsOn[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy_solid;
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy_definition;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs {
  __typename: "Output";
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_definition;
  dependedBy: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs_dependedBy[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_definition;
  isDynamicMapped: boolean;
  inputs: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_inputs[];
  outputs: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid_outputs[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles_solid;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob {
  __typename: "Job";
  id: string;
  name: string;
  description: string | null;
  modes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_modes[];
  solidHandles: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob_solidHandles[];
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  assetGroupJob: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes_assetGroupJob | null;
}

export interface InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export type InstanceAssetOpsQuery_repositoriesOrError = InstanceAssetOpsQuery_repositoriesOrError_PythonError | InstanceAssetOpsQuery_repositoriesOrError_RepositoryConnection;

export interface InstanceAssetOpsQuery {
  repositoriesOrError: InstanceAssetOpsQuery_repositoriesOrError;
}
