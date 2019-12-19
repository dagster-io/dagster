// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerEnvironmentSchemaFragment
// ====================================================

export interface PipelineExecutionContainerEnvironmentSchemaFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_rootEnvironmentType {
  __typename: "CompositeConfigType" | "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType {
  __typename: "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  values: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType;

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema {
  __typename: "EnvironmentSchema";
  rootEnvironmentType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_rootEnvironmentType;
  allConfigTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type PipelineExecutionContainerEnvironmentSchemaFragment = PipelineExecutionContainerEnvironmentSchemaFragment_PipelineNotFoundError | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema | PipelineExecutionContainerEnvironmentSchemaFragment_ModeNotFoundError;
