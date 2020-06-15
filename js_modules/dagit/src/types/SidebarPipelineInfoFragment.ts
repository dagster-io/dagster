// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarPipelineInfoFragment
// ====================================================

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarPipelineInfoFragment_modes_resources_configField_configType = SidebarPipelineInfoFragment_modes_resources_configField_configType_ArrayConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_EnumConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_RegularConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_CompositeConfigType | SidebarPipelineInfoFragment_modes_resources_configField_configType_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineInfoFragment_modes_resources_configField_configType;
}

export interface SidebarPipelineInfoFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarPipelineInfoFragment_modes_resources_configField | null;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarPipelineInfoFragment_modes_loggers_configField_configType = SidebarPipelineInfoFragment_modes_loggers_configField_configType_ArrayConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_EnumConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_RegularConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_CompositeConfigType | SidebarPipelineInfoFragment_modes_loggers_configField_configType_ScalarUnionConfigType;

export interface SidebarPipelineInfoFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineInfoFragment_modes_loggers_configField_configType;
}

export interface SidebarPipelineInfoFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarPipelineInfoFragment_modes_loggers_configField | null;
}

export interface SidebarPipelineInfoFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: SidebarPipelineInfoFragment_modes_resources[];
  loggers: SidebarPipelineInfoFragment_modes_loggers[];
}

export interface SidebarPipelineInfoFragment {
  __typename: "Pipeline" | "PipelineSnapshot";
  name: string;
  description: string | null;
  modes: SidebarPipelineInfoFragment_modes[];
}
