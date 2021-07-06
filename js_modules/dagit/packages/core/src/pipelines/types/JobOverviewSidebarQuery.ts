// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, PipelineRunStatus, InstigationStatus } from "./../../types/globalTypes";

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

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin_repositoryLocationMetadata[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError_cause | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PipelineRunStatsSnapshot | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets_key {
  __typename: "AssetKey";
  path: string[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets {
  __typename: "Asset";
  id: string;
  key: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets_key;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  rootRunId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string | null;
  mode: string;
  canTerminate: boolean;
  tags: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_tags[];
  status: PipelineRunStatus;
  repositoryOrigin: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin | null;
  stats: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats;
  assets: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PythonError | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PipelineRunStatsSnapshot;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns {
  __typename: "PipelineRun";
  id: string;
  stats: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  runsCount: number;
  lastRuns: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns[];
  runs: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs[];
  status: InstigationStatus;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks_results[];
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  mode: string;
  scheduleState: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState;
  futureTicks: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
}

export type JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PythonError | JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PipelineRunStatsSnapshot;

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns {
  __typename: "PipelineRun";
  id: string;
  stats: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  runsCount: number;
  lastRuns: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns[];
  runs: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_runs[];
  status: InstigationStatus;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  mode: string | null;
  sensorState: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState;
  nextTick: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_nextTick | null;
}

export interface JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  modes: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_modes[];
  runs: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs[];
  schedules: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules[];
  sensors: JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors[];
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
  limit: number;
}
