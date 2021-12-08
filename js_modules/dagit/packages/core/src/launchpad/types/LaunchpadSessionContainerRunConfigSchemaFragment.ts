/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchpadSessionContainerRunConfigSchemaFragment
// ====================================================

export interface LaunchpadSessionContainerRunConfigSchemaFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_rootConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType_values[];
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes = LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ArrayConfigType | LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_RegularConfigType | LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType | LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType | LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ScalarUnionConfigType;

export interface LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema {
  __typename: "RunConfigSchema";
  rootConfigType: LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_rootConfigType;
  allConfigTypes: LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema_allConfigTypes[];
}

export interface LaunchpadSessionContainerRunConfigSchemaFragment_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type LaunchpadSessionContainerRunConfigSchemaFragment = LaunchpadSessionContainerRunConfigSchemaFragment_PipelineNotFoundError | LaunchpadSessionContainerRunConfigSchemaFragment_RunConfigSchema | LaunchpadSessionContainerRunConfigSchemaFragment_ModeNotFoundError;
