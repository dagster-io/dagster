/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { GraphSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: GraphExplorerRootQuery
// ====================================================

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType = GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField_configType;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: GraphExplorerRootQuery_graphOrError_Graph_modes_resources_configField | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType = GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ArrayConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_EnumConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_RegularConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_CompositeConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_ScalarUnionConfigType | GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType_MapConfigType;

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField_configType;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers_configField | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: GraphExplorerRootQuery_graphOrError_Graph_modes_resources[];
  loggers: GraphExplorerRootQuery_graphOrError_Graph_modes_loggers[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs {
  __typename: "Input";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_solid;
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs {
  __typename: "Output";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_definition;
  dependedBy: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  inputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  configField: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition = GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition | GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition;

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_inputs[];
  outputs: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_outputs[];
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid_definition;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandle_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn_definition;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs {
  __typename: "Input";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs_dependsOn[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy_solid;
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy_definition;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs {
  __typename: "Output";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_definition;
  dependedBy: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs_dependedBy[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_configField_configType;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_metadata[];
  assetNodes: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_assetNodes[];
  inputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_outputDefinitions[];
  configField: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition_configField | null;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition = GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_SolidDefinition | GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition_CompositeSolidDefinition;

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_inputs[];
  outputs: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_outputs[];
  definition: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid_definition;
}

export interface GraphExplorerRootQuery_graphOrError_Graph_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: GraphExplorerRootQuery_graphOrError_Graph_solidHandles_solid;
}

export interface GraphExplorerRootQuery_graphOrError_Graph {
  __typename: "Graph";
  id: string;
  name: string;
  description: string | null;
  modes: GraphExplorerRootQuery_graphOrError_Graph_modes[];
  solidHandle: GraphExplorerRootQuery_graphOrError_Graph_solidHandle | null;
  solidHandles: GraphExplorerRootQuery_graphOrError_Graph_solidHandles[];
}

export interface GraphExplorerRootQuery_graphOrError_GraphNotFoundError {
  __typename: "GraphNotFoundError";
  message: string;
}

export interface GraphExplorerRootQuery_graphOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface GraphExplorerRootQuery_graphOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: GraphExplorerRootQuery_graphOrError_PythonError_cause | null;
}

export type GraphExplorerRootQuery_graphOrError = GraphExplorerRootQuery_graphOrError_Graph | GraphExplorerRootQuery_graphOrError_GraphNotFoundError | GraphExplorerRootQuery_graphOrError_PythonError;

export interface GraphExplorerRootQuery {
  graphOrError: GraphExplorerRootQuery_graphOrError;
}

export interface GraphExplorerRootQueryVariables {
  graphSelector?: GraphSelector | null;
  rootHandleID: string;
  requestScopeHandleID?: string | null;
}
