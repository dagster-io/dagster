/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarOpFragment
// ====================================================

export interface SidebarOpFragment_solidHandle_solid_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarOpFragment_solidHandle_solid_inputs_definition_type;
}

export interface SidebarOpFragment_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarOpFragment_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarOpFragment_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarOpFragment_solidHandle_solid_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarOpFragment_solidHandle_solid_inputs_definition;
  dependsOn: SidebarOpFragment_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarOpFragment_solidHandle_solid_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarOpFragment_solidHandle_solid_outputs_definition_type;
}

export interface SidebarOpFragment_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarOpFragment_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarOpFragment_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarOpFragment_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarOpFragment_solidHandle_solid_outputs_definition;
  dependedBy: SidebarOpFragment_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType | SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_MapConfigType;

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarOpFragment_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  requiredResources: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarOpFragment_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  id: string;
  inputMappings: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarOpFragment_solidHandle_solid_definition = SidebarOpFragment_solidHandle_solid_definition_SolidDefinition | SidebarOpFragment_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarOpFragment_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarOpFragment_solidHandle_solid_inputs[];
  outputs: SidebarOpFragment_solidHandle_solid_outputs[];
  definition: SidebarOpFragment_solidHandle_solid_definition;
}

export interface SidebarOpFragment_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarOpFragment_solidHandle_solid;
}

export interface SidebarOpFragment {
  __typename: "Pipeline" | "Job" | "PipelineSnapshot" | "Graph" | "CompositeSolidDefinition";
  id: string;
  name: string;
  solidHandle: SidebarOpFragment_solidHandle | null;
}
