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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

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

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType;

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

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  modes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError";
  message: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineNotFoundError | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | JobOverviewSidebarQuery_pipelineSnapshotOrError_PythonError;

export interface JobOverviewSidebarQuery {
  pipelineSnapshotOrError: JobOverviewSidebarQuery_pipelineSnapshotOrError;
}

export interface JobOverviewSidebarQueryVariables {
  pipelineSelector: PipelineSelector;
}
