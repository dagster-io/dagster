/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarModeInfoFragment
// ====================================================

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarModeInfoFragment_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarModeInfoFragment_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarModeInfoFragment_resources_configField_configType = SidebarModeInfoFragment_resources_configField_configType_ArrayConfigType | SidebarModeInfoFragment_resources_configField_configType_EnumConfigType | SidebarModeInfoFragment_resources_configField_configType_RegularConfigType | SidebarModeInfoFragment_resources_configField_configType_CompositeConfigType | SidebarModeInfoFragment_resources_configField_configType_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarModeInfoFragment_resources_configField_configType;
}

export interface SidebarModeInfoFragment_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarModeInfoFragment_resources_configField | null;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarModeInfoFragment_loggers_configField_configType = SidebarModeInfoFragment_loggers_configField_configType_ArrayConfigType | SidebarModeInfoFragment_loggers_configField_configType_EnumConfigType | SidebarModeInfoFragment_loggers_configField_configType_RegularConfigType | SidebarModeInfoFragment_loggers_configField_configType_CompositeConfigType | SidebarModeInfoFragment_loggers_configField_configType_ScalarUnionConfigType;

export interface SidebarModeInfoFragment_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarModeInfoFragment_loggers_configField_configType;
}

export interface SidebarModeInfoFragment_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarModeInfoFragment_loggers_configField | null;
}

export interface SidebarModeInfoFragment {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: SidebarModeInfoFragment_resources[];
  loggers: SidebarModeInfoFragment_loggers[];
}
