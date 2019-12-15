// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SolidsRootQuery
// ====================================================

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidsRootQuery_usedSolids_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidsRootQuery_usedSolids_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType;

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export type SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType = SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_EnumConfigType | SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType_CompositeConfigType;

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField_configType;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SolidsRootQuery_usedSolids_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: SolidsRootQuery_usedSolids_definition_SolidDefinition_metadata[];
  inputDefinitions: SolidsRootQuery_usedSolids_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: SolidsRootQuery_usedSolids_definition_SolidDefinition_outputDefinitions[];
  description: string | null;
  configField: SolidsRootQuery_usedSolids_definition_SolidDefinition_configField | null;
  requiredResources: SolidsRootQuery_usedSolids_definition_SolidDefinition_requiredResources[];
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputDefinitions[];
  description: string | null;
  requiredResources: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_requiredResources[];
  inputMappings: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition_outputMappings[];
}

export type SolidsRootQuery_usedSolids_definition = SolidsRootQuery_usedSolids_definition_SolidDefinition | SolidsRootQuery_usedSolids_definition_CompositeSolidDefinition;

export interface SolidsRootQuery_usedSolids_invocations_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface SolidsRootQuery_usedSolids_invocations_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface SolidsRootQuery_usedSolids_invocations {
  __typename: "SolidInvocationSite";
  pipeline: SolidsRootQuery_usedSolids_invocations_pipeline;
  solidHandle: SolidsRootQuery_usedSolids_invocations_solidHandle;
}

export interface SolidsRootQuery_usedSolids {
  __typename: "UsedSolid";
  definition: SolidsRootQuery_usedSolids_definition;
  invocations: SolidsRootQuery_usedSolids_invocations[];
}

export interface SolidsRootQuery {
  usedSolids: SolidsRootQuery_usedSolids[];
}
