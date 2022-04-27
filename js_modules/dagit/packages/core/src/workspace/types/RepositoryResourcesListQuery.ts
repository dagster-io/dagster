/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositoryResourcesListQuery
// ====================================================

export interface RepositoryResourcesListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType = RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ArrayConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_EnumConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_RegularConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_CompositeConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_ScalarUnionConfigType | RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType_MapConfigType;

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField {
  __typename: "ConfigTypeField";
  configType: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField_configType;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources_configField | null;
}

export interface RepositoryResourcesListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  defaultResources: RepositoryResourcesListQuery_repositoryOrError_Repository_defaultResources[];
}

export interface RepositoryResourcesListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositoryResourcesListQuery_repositoryOrError = RepositoryResourcesListQuery_repositoryOrError_PythonError | RepositoryResourcesListQuery_repositoryOrError_Repository | RepositoryResourcesListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositoryResourcesListQuery {
  repositoryOrError: RepositoryResourcesListQuery_repositoryOrError;
}

export interface RepositoryResourcesListQueryVariables {
  repositorySelector: RepositorySelector;
}
