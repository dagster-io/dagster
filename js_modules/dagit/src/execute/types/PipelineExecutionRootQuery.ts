// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExecutionRootQuery
// ====================================================

export interface PipelineExecutionRootQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "SolidNotFoundError";
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_EnumConfigType_values[];
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  ofType: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType = PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes = PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_RegularConfigType | PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_EnumConfigType | PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes_CompositeConfigType;

export interface PipelineExecutionRootQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  modes: PipelineExecutionRootQuery_pipelineOrError_Pipeline_modes[];
  environmentType: PipelineExecutionRootQuery_pipelineOrError_Pipeline_environmentType;
  configTypes: PipelineExecutionRootQuery_pipelineOrError_Pipeline_configTypes[];
}

export interface PipelineExecutionRootQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export type PipelineExecutionRootQuery_pipelineOrError = PipelineExecutionRootQuery_pipelineOrError_PythonError | PipelineExecutionRootQuery_pipelineOrError_Pipeline | PipelineExecutionRootQuery_pipelineOrError_PipelineNotFoundError;

export interface PipelineExecutionRootQuery {
  pipelineOrError: PipelineExecutionRootQuery_pipelineOrError;
}

export interface PipelineExecutionRootQueryVariables {
  name: string;
  solidSubset?: string[] | null;
  mode?: string | null;
}
