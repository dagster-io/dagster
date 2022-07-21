/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarRootContainerFragment
// ====================================================

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType = SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarRootContainerFragment_Pipeline_modes_resources_configField_configType;
}

export interface SidebarRootContainerFragment_Pipeline_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarRootContainerFragment_Pipeline_modes_resources_configField | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType = SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType | SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType;

export interface SidebarRootContainerFragment_Pipeline_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarRootContainerFragment_Pipeline_modes_loggers_configField_configType;
}

export interface SidebarRootContainerFragment_Pipeline_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarRootContainerFragment_Pipeline_modes_loggers_configField | null;
}

export interface SidebarRootContainerFragment_Pipeline_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: SidebarRootContainerFragment_Pipeline_modes_resources[];
  loggers: SidebarRootContainerFragment_Pipeline_modes_loggers[];
}

export interface SidebarRootContainerFragment_Pipeline {
  __typename: "Pipeline" | "Job" | "Graph" | "CompositeSolidDefinition";
  id: string;
  name: string;
  description: string | null;
  modes: SidebarRootContainerFragment_Pipeline_modes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType = SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField_configType;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarRootContainerFragment_PipelineSnapshot_modes_resources_configField | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType = SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType | SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType;

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField_configType;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers_configField | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: SidebarRootContainerFragment_PipelineSnapshot_modes_resources[];
  loggers: SidebarRootContainerFragment_PipelineSnapshot_modes_loggers[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type SidebarRootContainerFragment_PipelineSnapshot_metadataEntries = SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_PathMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_JsonMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_UrlMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TextMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_FloatMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_IntMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_BoolMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry | SidebarRootContainerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry;

export interface SidebarRootContainerFragment_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  modes: SidebarRootContainerFragment_PipelineSnapshot_modes[];
  pipelineSnapshotId: string;
  parentSnapshotId: string | null;
  metadataEntries: SidebarRootContainerFragment_PipelineSnapshot_metadataEntries[];
}

export type SidebarRootContainerFragment = SidebarRootContainerFragment_Pipeline | SidebarRootContainerFragment_PipelineSnapshot;
