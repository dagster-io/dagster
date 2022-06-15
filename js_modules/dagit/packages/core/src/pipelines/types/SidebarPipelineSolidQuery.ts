/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarPipelineSolidQuery
// ====================================================

export interface SidebarPipelineSolidQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition_type;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_definition;
  dependsOn: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition_type;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_definition;
  dependedBy: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  requiredResources: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  id: string;
  inputMappings: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition = SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_SolidDefinition | SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_inputs[];
  outputs: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_outputs[];
  definition: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid_definition;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle_solid;
}

export interface SidebarPipelineSolidQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  solidHandle: SidebarPipelineSolidQuery_pipelineOrError_Pipeline_solidHandle | null;
}

export type SidebarPipelineSolidQuery_pipelineOrError = SidebarPipelineSolidQuery_pipelineOrError_PipelineNotFoundError | SidebarPipelineSolidQuery_pipelineOrError_Pipeline;

export interface SidebarPipelineSolidQuery {
  pipelineOrError: SidebarPipelineSolidQuery_pipelineOrError;
}

export interface SidebarPipelineSolidQueryVariables {
  selector: PipelineSelector;
  handleID: string;
}
