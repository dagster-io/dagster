// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineDetailsFragment
// ====================================================

export interface PipelineDetailsFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineDetailsFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineDetailsFragment_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineDetailsFragment_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineDetailsFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineDetailsFragment_configTypes_EnumConfigType_values[];
}

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  ofType: PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType = PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineDetailsFragment_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineDetailsFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineDetailsFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineDetailsFragment_configTypes_CompositeConfigType_fields[];
}

export type PipelineDetailsFragment_configTypes = PipelineDetailsFragment_configTypes_RegularConfigType | PipelineDetailsFragment_configTypes_EnumConfigType | PipelineDetailsFragment_configTypes_CompositeConfigType;

export interface PipelineDetailsFragment {
  __typename: "Pipeline";
  name: string;
  modes: PipelineDetailsFragment_modes[];
  environmentType: PipelineDetailsFragment_environmentType;
  configTypes: PipelineDetailsFragment_configTypes[];
}
