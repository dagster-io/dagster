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
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType" | "ScalarUnionConfigType";
  key: string;
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes = ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ArrayConfigType | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType | ExecutionSessionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ScalarUnionConfigType;

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
