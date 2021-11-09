// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidContainerFragment
// ====================================================

export interface SidebarSolidContainerFragment_solidHandle_solid_inputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarSolidContainerFragment_solidHandle_solid_inputs_definition_type;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarSolidContainerFragment_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarSolidContainerFragment_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_inputs {
  __typename: "Input";
  isDynamicCollect: boolean;
  definition: SidebarSolidContainerFragment_solidHandle_solid_inputs_definition;
  dependsOn: SidebarSolidContainerFragment_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_outputs_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  isDynamic: boolean | null;
  type: SidebarSolidContainerFragment_solidHandle_solid_outputs_definition_type;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarSolidContainerFragment_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarSolidContainerFragment_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarSolidContainerFragment_solidHandle_solid_outputs_definition;
  dependedBy: SidebarSolidContainerFragment_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType;

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_metadata[];
  requiredResources: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
  isDynamic: boolean | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  inputMappings: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarSolidContainerFragment_solidHandle_solid_definition = SidebarSolidContainerFragment_solidHandle_solid_definition_SolidDefinition | SidebarSolidContainerFragment_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarSolidContainerFragment_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarSolidContainerFragment_solidHandle_solid_inputs[];
  outputs: SidebarSolidContainerFragment_solidHandle_solid_outputs[];
  definition: SidebarSolidContainerFragment_solidHandle_solid_definition;
}

export interface SidebarSolidContainerFragment_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarSolidContainerFragment_solidHandle_solid;
}

export interface SidebarSolidContainerFragment {
  __typename: "Pipeline" | "Job" | "PipelineSnapshot" | "Graph" | "CompositeSolidDefinition";
  id: string;
  name: string;
  solidHandle: SidebarSolidContainerFragment_solidHandle | null;
}
