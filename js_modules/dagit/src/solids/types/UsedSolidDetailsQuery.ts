// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: UsedSolidDetailsQuery
// ====================================================

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType;

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export type UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType = UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType | UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType;

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField_configType;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_metadata[];
  inputDefinitions: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_outputDefinitions[];
  description: string | null;
  configField: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_configField | null;
  requiredResources: UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition_requiredResources[];
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputDefinitions[];
  description: string | null;
  requiredResources: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_requiredResources[];
  inputMappings: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition_outputMappings[];
}

export type UsedSolidDetailsQuery_usedSolid_definition = UsedSolidDetailsQuery_usedSolid_definition_SolidDefinition | UsedSolidDetailsQuery_usedSolid_definition_CompositeSolidDefinition;

export interface UsedSolidDetailsQuery_usedSolid_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface UsedSolidDetailsQuery_usedSolid_invocations_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface UsedSolidDetailsQuery_usedSolid_invocations {
  __typename: "SolidInvocationSite";
  pipeline: UsedSolidDetailsQuery_usedSolid_invocations_pipeline;
  solidHandle: UsedSolidDetailsQuery_usedSolid_invocations_solidHandle;
}

export interface UsedSolidDetailsQuery_usedSolid {
  __typename: "UsedSolid";
  definition: UsedSolidDetailsQuery_usedSolid_definition;
  invocations: UsedSolidDetailsQuery_usedSolid_invocations[];
}

export interface UsedSolidDetailsQuery {
  usedSolid: UsedSolidDetailsQuery_usedSolid | null;
}

export interface UsedSolidDetailsQueryVariables {
  name: string;
}
