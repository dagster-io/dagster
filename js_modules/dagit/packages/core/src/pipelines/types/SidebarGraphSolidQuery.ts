/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { GraphSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarGraphSolidQuery
// ====================================================

export interface SidebarGraphSolidQuery_graphOrError_GraphNotFoundError {
  __typename: "GraphNotFoundError" | "PythonError";
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_definition_type;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_definition;
  dependsOn: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_definition_type;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_definition;
  dependedBy: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  requiredResources: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  id: string;
  inputMappings: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition = SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_SolidDefinition | SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_inputs[];
  outputs: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_outputs[];
  definition: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid_definition;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle_solid;
}

export interface SidebarGraphSolidQuery_graphOrError_Graph {
  __typename: "Graph";
  id: string;
  name: string;
  solidHandle: SidebarGraphSolidQuery_graphOrError_Graph_solidHandle | null;
}

export type SidebarGraphSolidQuery_graphOrError = SidebarGraphSolidQuery_graphOrError_GraphNotFoundError | SidebarGraphSolidQuery_graphOrError_Graph;

export interface SidebarGraphSolidQuery {
  graphOrError: SidebarGraphSolidQuery_graphOrError;
}

export interface SidebarGraphSolidQueryVariables {
  selector: GraphSelector;
  handleID: string;
}
