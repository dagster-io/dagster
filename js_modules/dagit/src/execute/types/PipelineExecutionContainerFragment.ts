/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerFragment
// ====================================================

export interface PipelineExecutionContainerFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionContainerFragment_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionContainerFragment_configTypes_EnumConfigType_values[];
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  ofType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType = PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_configTypes = PipelineExecutionContainerFragment_configTypes_RegularConfigType | PipelineExecutionContainerFragment_configTypes_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment {
  __typename: "Pipeline";
  name: string;
  environmentType: PipelineExecutionContainerFragment_environmentType;
  configTypes: PipelineExecutionContainerFragment_configTypes[];
}
