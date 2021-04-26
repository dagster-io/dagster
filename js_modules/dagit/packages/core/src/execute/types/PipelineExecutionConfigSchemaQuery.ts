// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineExecutionConfigSchemaQuery
// ====================================================

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_rootConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType_values[];
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes = PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ArrayConfigType | PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_RegularConfigType | PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType | PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType | PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ScalarUnionConfigType;

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema {
  __typename: "RunConfigSchema";
  rootConfigType: PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_rootConfigType;
  allConfigTypes: PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes[];
}

export interface PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError = PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_PipelineNotFoundError | PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_RunConfigSchema | PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError_ModeNotFoundError;

export interface PipelineExecutionConfigSchemaQuery {
  runConfigSchemaOrError: PipelineExecutionConfigSchemaQuery_runConfigSchemaOrError;
}

export interface PipelineExecutionConfigSchemaQueryVariables {
  selector: PipelineSelector;
  mode?: string | null;
}
