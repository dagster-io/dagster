/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: BackfillSelectorQuery
// ====================================================

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PipelineSnapshotNotFoundError" | "PythonError";
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition;
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_definition;
  dependedBy: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_metadata[];
  assetNodes: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes[];
  inputDefinitions: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions[];
  configField: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField | null;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition = BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition | BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition;

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  solidHandles: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export type BackfillSelectorQuery_pipelineSnapshotOrError = BackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError | BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface BackfillSelectorQuery_instance_runLauncher {
  __typename: "RunLauncher";
  name: string;
}

export interface BackfillSelectorQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  healthy: boolean | null;
}

export interface BackfillSelectorQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  daemonStatus: BackfillSelectorQuery_instance_daemonHealth_daemonStatus;
}

export interface BackfillSelectorQuery_instance {
  __typename: "Instance";
  runLauncher: BackfillSelectorQuery_instance_runLauncher | null;
  daemonHealth: BackfillSelectorQuery_instance_daemonHealth;
  runQueuingSupported: boolean;
}

export interface BackfillSelectorQuery {
  pipelineSnapshotOrError: BackfillSelectorQuery_pipelineSnapshotOrError;
  instance: BackfillSelectorQuery_instance;
}

export interface BackfillSelectorQueryVariables {
  pipelineSelector: PipelineSelector;
}
