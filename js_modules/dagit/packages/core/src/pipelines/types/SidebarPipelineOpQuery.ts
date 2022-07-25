/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarPipelineOpQuery
// ====================================================

export interface SidebarPipelineOpQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition_type;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition;
  dependsOn: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition_type;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition;
  dependedBy: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  requiredResources: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  id: string;
  inputMappings: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition = SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition | SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs[];
  outputs: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs[];
  definition: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid_definition;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle_solid;
}

export interface SidebarPipelineOpQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  solidHandle: SidebarPipelineOpQuery_pipelineOrError_Pipeline_solidHandle | null;
}

export type SidebarPipelineOpQuery_pipelineOrError = SidebarPipelineOpQuery_pipelineOrError_PipelineNotFoundError | SidebarPipelineOpQuery_pipelineOrError_Pipeline;

export interface SidebarPipelineOpQuery {
  pipelineOrError: SidebarPipelineOpQuery_pipelineOrError;
}

export interface SidebarPipelineOpQueryVariables {
  selector: PipelineSelector;
  handleID: string;
}
