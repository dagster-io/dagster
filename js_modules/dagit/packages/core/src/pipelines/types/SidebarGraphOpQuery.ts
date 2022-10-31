/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { GraphSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarGraphOpQuery
// ====================================================

export interface SidebarGraphOpQuery_graphOrError_GraphNotFoundError {
  __typename: "GraphNotFoundError" | "PythonError";
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_definition_type;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_definition;
  dependsOn: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_definition_type;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_definition;
  dependedBy: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  requiredResources: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  id: string;
  inputMappings: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition = SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition | SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_inputs[];
  outputs: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_outputs[];
  definition: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid_definition;
}

export interface SidebarGraphOpQuery_graphOrError_Graph_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarGraphOpQuery_graphOrError_Graph_solidHandle_solid;
}

export interface SidebarGraphOpQuery_graphOrError_Graph {
  __typename: "Graph";
  id: string;
  name: string;
  solidHandle: SidebarGraphOpQuery_graphOrError_Graph_solidHandle | null;
}

export type SidebarGraphOpQuery_graphOrError = SidebarGraphOpQuery_graphOrError_GraphNotFoundError | SidebarGraphOpQuery_graphOrError_Graph;

export interface SidebarGraphOpQuery {
  graphOrError: SidebarGraphOpQuery_graphOrError;
}

export interface SidebarGraphOpQueryVariables {
  selector: GraphSelector;
  handleID: string;
}
