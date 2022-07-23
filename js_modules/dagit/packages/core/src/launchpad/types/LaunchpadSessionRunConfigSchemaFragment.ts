/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchpadSessionRunConfigSchemaFragment
// ====================================================

export interface LaunchpadSessionRunConfigSchemaFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_rootConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType_values[];
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes = LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ArrayConfigType | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_RegularConfigType | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_MapConfigType | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_EnumConfigType | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_CompositeConfigType | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes_ScalarUnionConfigType;

export interface LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema {
  __typename: "RunConfigSchema";
  rootConfigType: LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_rootConfigType;
  allConfigTypes: LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_allConfigTypes[];
}

export interface LaunchpadSessionRunConfigSchemaFragment_ModeNotFoundError {
  __typename: "ModeNotFoundError";
  message: string;
}

export type LaunchpadSessionRunConfigSchemaFragment = LaunchpadSessionRunConfigSchemaFragment_PipelineNotFoundError | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema | LaunchpadSessionRunConfigSchemaFragment_ModeNotFoundError;
