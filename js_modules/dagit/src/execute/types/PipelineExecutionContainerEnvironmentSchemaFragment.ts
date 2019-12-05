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
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType_innerTypes[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType_ofType;
}

export interface PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
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
  isList: boolean;
  isSelector: boolean;
  isNullable: boolean;
  description: string | null;
  innerTypes: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_innerTypes[];
  values: PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType_values[];
}

export type PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes = PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_RegularConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_CompositeConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_ListConfigType | PipelineExecutionContainerEnvironmentSchemaFragment_EnvironmentSchema_allConfigTypes_EnumConfigType;

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
