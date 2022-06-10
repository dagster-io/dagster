/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: JobOverviewSidebarQuery
// ====================================================

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources[];
  loggers: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PathMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_JsonMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_UrlMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TextMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_FloatMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_IntMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_BoolMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  modes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes[];
  metadataEntries: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError";
  message: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobOverviewSidebarQuery_pipelineSnapshotOrError_PythonError_cause | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineNotFoundError | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | JobOverviewSidebarQuery_pipelineSnapshotOrError_PythonError;

export interface JobOverviewSidebarQuery {
  pipelineSnapshotOrError: JobOverviewSidebarQuery_pipelineSnapshotOrError;
}

export interface JobOverviewSidebarQueryVariables {
  pipelineSelector: PipelineSelector;
}
