/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExecutionRootQuery
// ====================================================

export interface PipelineExecutionRootQuery_pipeline_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType_values[];
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  ofType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType = PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionRootQuery_pipeline_configTypes = PipelineExecutionRootQuery_pipeline_configTypes_RegularConfigType | PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType;

export interface PipelineExecutionRootQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  environmentType: PipelineExecutionRootQuery_pipeline_environmentType;
  configTypes: PipelineExecutionRootQuery_pipeline_configTypes[];
}

export interface PipelineExecutionRootQuery {
  pipeline: PipelineExecutionRootQuery_pipeline;
}

export interface PipelineExecutionRootQueryVariables {
  name: string;
  solidSubset?: string[] | null;
}
