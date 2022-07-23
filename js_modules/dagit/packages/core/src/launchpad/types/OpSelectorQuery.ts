/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: OpSelectorQuery
// ====================================================

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition;
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_solid;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs {
  __typename: "Input";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_solid;
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs {
  __typename: "Output";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_definition;
  dependedBy: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configField_configType;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_metadata[];
  assetNodes: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_assetNodes[];
  inputDefinitions: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_outputDefinitions[];
  configField: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configField | null;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition = OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition | OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition;

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs[];
  outputs: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs[];
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid_definition;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles_solid;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  solidHandles: OpSelectorQuery_pipelineOrError_Pipeline_solidHandles[];
}

export interface OpSelectorQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface OpSelectorQuery_pipelineOrError_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface OpSelectorQuery_pipelineOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OpSelectorQuery_pipelineOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OpSelectorQuery_pipelineOrError_PythonError_causes[];
}

export type OpSelectorQuery_pipelineOrError = OpSelectorQuery_pipelineOrError_Pipeline | OpSelectorQuery_pipelineOrError_PipelineNotFoundError | OpSelectorQuery_pipelineOrError_InvalidSubsetError | OpSelectorQuery_pipelineOrError_PythonError;

export interface OpSelectorQuery {
  pipelineOrError: OpSelectorQuery_pipelineOrError;
}

export interface OpSelectorQueryVariables {
  selector: PipelineSelector;
  requestScopeHandleID?: string | null;
}
