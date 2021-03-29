// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ExecutionSessionContainerRunConfigSchemaFragment
// ====================================================

export interface ExecutionSessionContainerRunConfigSchemaFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_rootConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType_values[];
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes = ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ArrayConfigType | ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_RegularConfigType | ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType | ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType | ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ScalarUnionConfigType;

export interface ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema {
  __typename: "RunConfigSchema";
  rootConfigType: ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_rootConfigType;
  allConfigTypes: ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes[];
}

export interface ExecutionSessionContainerRunConfigSchemaFragment_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type ExecutionSessionContainerRunConfigSchemaFragment = ExecutionSessionContainerRunConfigSchemaFragment_PipelineNotFoundError | ExecutionSessionContainerRunConfigSchemaFragment_RunConfigSchema | ExecutionSessionContainerRunConfigSchemaFragment_ModeNotFoundError;
