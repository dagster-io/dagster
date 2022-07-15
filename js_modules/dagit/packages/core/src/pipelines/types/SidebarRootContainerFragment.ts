/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarRootContainerFragment
// ====================================================

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarRootContainerFragment_modes_resources_configField_configType = SidebarRootContainerFragment_modes_resources_configField_configType_ArrayConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_EnumConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_RegularConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_CompositeConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_ScalarUnionConfigType | SidebarRootContainerFragment_modes_resources_configField_configType_MapConfigType;

export interface SidebarRootContainerFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarRootContainerFragment_modes_resources_configField_configType;
}

export interface SidebarRootContainerFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarRootContainerFragment_modes_resources_configField | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarRootContainerFragment_modes_loggers_configField_configType = SidebarRootContainerFragment_modes_loggers_configField_configType_ArrayConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_EnumConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_RegularConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_CompositeConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_ScalarUnionConfigType | SidebarRootContainerFragment_modes_loggers_configField_configType_MapConfigType;

export interface SidebarRootContainerFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarRootContainerFragment_modes_loggers_configField_configType;
}

export interface SidebarRootContainerFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarRootContainerFragment_modes_loggers_configField | null;
}

export interface SidebarRootContainerFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: SidebarRootContainerFragment_modes_resources[];
  loggers: SidebarRootContainerFragment_modes_loggers[];
}

export interface SidebarRootContainerFragment {
  __typename: "Pipeline" | "Job" | "PipelineSnapshot" | "Graph" | "CompositeSolidDefinition";
  id: string;
  name: string;
  description: string | null;
  modes: SidebarRootContainerFragment_modes[];
}
