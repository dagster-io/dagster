// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ExecutionSessionContainerEnvironmentSchemaFragment
// ====================================================

export interface ExecutionSessionContainerEnvironmentSchemaFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_rootEnvironmentType {
  __typename: "CompositeConfigType" | "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType {
  __typename: "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  values: ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values[];
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields[];
}

export type ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes = ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType;

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema {
  __typename: "EnvironmentSchema";
  rootEnvironmentType: ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_rootEnvironmentType;
  allConfigTypes: ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes[];
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type ExecutionSessionContainerEnvironmentSchemaFragment = ExecutionSessionContainerEnvironmentSchemaFragment_PipelineNotFoundError | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema | ExecutionSessionContainerEnvironmentSchemaFragment_ModeNotFoundError;
