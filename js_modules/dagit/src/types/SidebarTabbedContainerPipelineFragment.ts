// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerPipelineFragment
// ====================================================

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType = SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerPipelineFragment_modes_resources_configField_configType;
}

export interface SidebarTabbedContainerPipelineFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: SidebarTabbedContainerPipelineFragment_modes_resources_configField | null;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType = SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ArrayConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_EnumConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_RegularConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_CompositeConfigType | SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType_ScalarUnionConfigType;

export interface SidebarTabbedContainerPipelineFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerPipelineFragment_modes_loggers_configField_configType;
}

export interface SidebarTabbedContainerPipelineFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: SidebarTabbedContainerPipelineFragment_modes_loggers_configField | null;
}

export interface SidebarTabbedContainerPipelineFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: SidebarTabbedContainerPipelineFragment_modes_resources[];
  loggers: SidebarTabbedContainerPipelineFragment_modes_loggers[];
}

export interface SidebarTabbedContainerPipelineFragment {
  __typename: "Pipeline" | "PipelineSnapshot";
  name: string;
  description: string | null;
  modes: SidebarTabbedContainerPipelineFragment_modes[];
}
