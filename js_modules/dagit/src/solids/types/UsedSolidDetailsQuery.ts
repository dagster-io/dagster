// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: UsedSolidDetailsQuery
// ====================================================

export interface UsedSolidDetailsQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ArrayConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_EnumConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_RegularConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_CompositeConfigType | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField_configType;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_metadata[];
  inputDefinitions: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_outputDefinitions[];
  description: string | null;
  configField: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_configField | null;
  requiredResources: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition_requiredResources[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputDefinitions[];
  description: string | null;
  inputMappings: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_outputMappings[];
  requiredResources: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition_requiredResources[];
}

export type UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition = UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_SolidDefinition | UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition_CompositeSolidDefinition;

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_invocations_pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_invocations_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_invocations {
  __typename: "SolidInvocationSite";
  pipeline: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_invocations_pipeline;
  solidHandle: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_invocations_solidHandle;
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid {
  __typename: "UsedSolid";
  definition: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_definition;
  invocations: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid_invocations[];
}

export interface UsedSolidDetailsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolid: UsedSolidDetailsQuery_repositoryOrError_Repository_usedSolid | null;
}

export type UsedSolidDetailsQuery_repositoryOrError = UsedSolidDetailsQuery_repositoryOrError_PythonError | UsedSolidDetailsQuery_repositoryOrError_Repository;

export interface UsedSolidDetailsQuery {
  repositoryOrError: UsedSolidDetailsQuery_repositoryOrError;
}

export interface UsedSolidDetailsQueryVariables {
  name: string;
  repositorySelector: RepositorySelector;
}
