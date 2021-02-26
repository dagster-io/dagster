// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SolidSelectorQuery
// ====================================================

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition_type;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition;
  solid: SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_solid;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs {
  __typename: "Input";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_definition;
  dependsOn: SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn[];
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition_type;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_solid;
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs {
  __typename: "Output";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_definition;
  dependedBy: SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy[];
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_inputDefinitions_type;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_outputDefinitions_type;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_configField_configType;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_metadata[];
  inputDefinitions: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_outputDefinitions[];
  configField: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition_configField | null;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition_outputMappings[];
}

export type SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition = SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_SolidDefinition | SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition_CompositeSolidDefinition;

export interface SolidSelectorQuery_pipelineOrError_Pipeline_solids {
  __typename: "Solid";
  name: string;
  inputs: SolidSelectorQuery_pipelineOrError_Pipeline_solids_inputs[];
  outputs: SolidSelectorQuery_pipelineOrError_Pipeline_solids_outputs[];
  definition: SolidSelectorQuery_pipelineOrError_Pipeline_solids_definition;
}

export interface SolidSelectorQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  solids: SolidSelectorQuery_pipelineOrError_Pipeline_solids[];
}

export interface SolidSelectorQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface SolidSelectorQuery_pipelineOrError_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface SolidSelectorQuery_pipelineOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type SolidSelectorQuery_pipelineOrError = SolidSelectorQuery_pipelineOrError_Pipeline | SolidSelectorQuery_pipelineOrError_PipelineNotFoundError | SolidSelectorQuery_pipelineOrError_InvalidSubsetError | SolidSelectorQuery_pipelineOrError_PythonError;

export interface SolidSelectorQuery {
  pipelineOrError: SolidSelectorQuery_pipelineOrError;
}

export interface SolidSelectorQueryVariables {
  selector: PipelineSelector;
}
