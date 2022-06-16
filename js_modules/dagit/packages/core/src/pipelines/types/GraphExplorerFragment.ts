/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: GraphExplorerFragment
// ====================================================

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerFragment_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerFragment_modes_resources_configField_configType = GraphExplorerFragment_modes_resources_configField_configType_ArrayConfigType | GraphExplorerFragment_modes_resources_configField_configType_EnumConfigType | GraphExplorerFragment_modes_resources_configField_configType_RegularConfigType | GraphExplorerFragment_modes_resources_configField_configType_CompositeConfigType | GraphExplorerFragment_modes_resources_configField_configType_ScalarUnionConfigType | GraphExplorerFragment_modes_resources_configField_configType_MapConfigType;

export interface GraphExplorerFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerFragment_modes_resources_configField_configType;
}

export interface GraphExplorerFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: GraphExplorerFragment_modes_resources_configField | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerFragment_modes_loggers_configField_configType = GraphExplorerFragment_modes_loggers_configField_configType_ArrayConfigType | GraphExplorerFragment_modes_loggers_configField_configType_EnumConfigType | GraphExplorerFragment_modes_loggers_configField_configType_RegularConfigType | GraphExplorerFragment_modes_loggers_configField_configType_CompositeConfigType | GraphExplorerFragment_modes_loggers_configField_configType_ScalarUnionConfigType | GraphExplorerFragment_modes_loggers_configField_configType_MapConfigType;

export interface GraphExplorerFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerFragment_modes_loggers_configField_configType;
}

export interface GraphExplorerFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: GraphExplorerFragment_modes_loggers_configField | null;
}

export interface GraphExplorerFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: GraphExplorerFragment_modes_resources[];
  loggers: GraphExplorerFragment_modes_loggers[];
}

export interface GraphExplorerFragment {
  __typename: "Pipeline" | "Job" | "PipelineSnapshot" | "Graph" | "CompositeSolidDefinition";
  id: string;
  name: string;
  description: string | null;
  modes: GraphExplorerFragment_modes[];
}
