/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: GraphExplorerFragment
// ====================================================

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerFragment_Pipeline_modes_resources_configField_configType = GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_EnumConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_RegularConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_resources_configField_configType_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerFragment_Pipeline_modes_resources_configField_configType;
}

export interface GraphExplorerFragment_Pipeline_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: GraphExplorerFragment_Pipeline_modes_resources_configField | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerFragment_Pipeline_modes_loggers_configField_configType = GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ArrayConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_EnumConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_RegularConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_CompositeConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_ScalarUnionConfigType | GraphExplorerFragment_Pipeline_modes_loggers_configField_configType_MapConfigType;

export interface GraphExplorerFragment_Pipeline_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerFragment_Pipeline_modes_loggers_configField_configType;
}

export interface GraphExplorerFragment_Pipeline_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: GraphExplorerFragment_Pipeline_modes_loggers_configField | null;
}

export interface GraphExplorerFragment_Pipeline_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: GraphExplorerFragment_Pipeline_modes_resources[];
  loggers: GraphExplorerFragment_Pipeline_modes_loggers[];
}

export interface GraphExplorerFragment_Pipeline {
  __typename: "Pipeline" | "Job" | "Graph" | "CompositeSolidDefinition";
  id: string;
  name: string;
  description: string | null;
  modes: GraphExplorerFragment_Pipeline_modes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType = GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField_configType;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: GraphExplorerFragment_PipelineSnapshot_modes_resources_configField | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType = GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType | GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType;

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField_configType;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: GraphExplorerFragment_PipelineSnapshot_modes_loggers_configField | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: GraphExplorerFragment_PipelineSnapshot_modes_resources[];
  loggers: GraphExplorerFragment_PipelineSnapshot_modes_loggers[];
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: GraphExplorerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry_table;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type GraphExplorerFragment_PipelineSnapshot_metadataEntries = GraphExplorerFragment_PipelineSnapshot_metadataEntries_PathMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_JsonMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_UrlMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_TextMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_FloatMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_IntMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_BoolMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_AssetMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableMetadataEntry | GraphExplorerFragment_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry;

export interface GraphExplorerFragment_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  modes: GraphExplorerFragment_PipelineSnapshot_modes[];
  pipelineSnapshotId: string;
  parentSnapshotId: string | null;
  metadataEntries: GraphExplorerFragment_PipelineSnapshot_metadataEntries[];
}

export type GraphExplorerFragment = GraphExplorerFragment_Pipeline | GraphExplorerFragment_PipelineSnapshot;
