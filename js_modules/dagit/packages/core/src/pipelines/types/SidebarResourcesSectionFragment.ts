/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarResourcesSectionFragment
// ====================================================

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarResourcesSectionFragment_resources_configField_configType = SidebarResourcesSectionFragment_resources_configField_configType_ArrayConfigType | SidebarResourcesSectionFragment_resources_configField_configType_EnumConfigType | SidebarResourcesSectionFragment_resources_configField_configType_RegularConfigType | SidebarResourcesSectionFragment_resources_configField_configType_CompositeConfigType | SidebarResourcesSectionFragment_resources_configField_configType_ScalarUnionConfigType | SidebarResourcesSectionFragment_resources_configField_configType_MapConfigType;

export interface SidebarResourcesSectionFragment_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarResourcesSectionFragment_resources_configField_configType;
}

export interface SidebarResourcesSectionFragment_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarResourcesSectionFragment_resources_configField | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes = SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarResourcesSectionFragment_loggers_configField_configType = SidebarResourcesSectionFragment_loggers_configField_configType_ArrayConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_EnumConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_RegularConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_CompositeConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_ScalarUnionConfigType | SidebarResourcesSectionFragment_loggers_configField_configType_MapConfigType;

export interface SidebarResourcesSectionFragment_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarResourcesSectionFragment_loggers_configField_configType;
}

export interface SidebarResourcesSectionFragment_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarResourcesSectionFragment_loggers_configField | null;
}

export interface SidebarResourcesSectionFragment {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: SidebarResourcesSectionFragment_resources[];
  loggers: SidebarResourcesSectionFragment_loggers[];
}
