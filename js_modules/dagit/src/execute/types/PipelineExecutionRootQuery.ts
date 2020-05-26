// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineExecutionRootQuery
// ====================================================

export interface PipelineExecutionRootQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionRootQuery_pipelineOrError_Pipeline_modes[];
  tags: PipelineExecutionRootQuery_pipelineOrError_Pipeline_tags[];
}

export interface PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError_pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError_pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError_pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError_pipeline_modes[];
  tags: PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError_pipeline_tags[];
}

export interface PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
  pipeline: PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError_pipeline;
}

export type PipelineExecutionRootQuery_pipelineOrError = PipelineExecutionRootQuery_pipelineOrError_PipelineNotFoundError | PipelineExecutionRootQuery_pipelineOrError_PythonError | PipelineExecutionRootQuery_pipelineOrError_Pipeline | PipelineExecutionRootQuery_pipelineOrError_InvalidSubsetError;

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_rootConfigType {
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType" | "ScalarUnionConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType_values[];
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes = PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ArrayConfigType | PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_RegularConfigType | PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_EnumConfigType | PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_CompositeConfigType | PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes_ScalarUnionConfigType;

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema {
  __typename: "RunConfigSchema";
  rootConfigType: PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_rootConfigType;
  allConfigTypes: PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema_allConfigTypes[];
}

export interface PipelineExecutionRootQuery_runConfigSchemaOrError_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type PipelineExecutionRootQuery_runConfigSchemaOrError = PipelineExecutionRootQuery_runConfigSchemaOrError_PipelineNotFoundError | PipelineExecutionRootQuery_runConfigSchemaOrError_RunConfigSchema | PipelineExecutionRootQuery_runConfigSchemaOrError_ModeNotFoundError;

export interface PipelineExecutionRootQuery {
  pipelineOrError: PipelineExecutionRootQuery_pipelineOrError;
  runConfigSchemaOrError: PipelineExecutionRootQuery_runConfigSchemaOrError;
}

export interface PipelineExecutionRootQueryVariables {
  selector: PipelineSelector;
  mode?: string | null;
}
