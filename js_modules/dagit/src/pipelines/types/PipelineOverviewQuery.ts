// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, PipelineRunStatus, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineOverviewQuery
// ====================================================

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition;
  solid: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_definition;
  dependsOn: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_definition;
  dependedBy: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField | null;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputMappings: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition;

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  inputs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
  definition: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  solid: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin_repositoryLocationMetadata[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError_cause | null;
}

export type PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PipelineRunStatsSnapshot | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PythonError;

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets_key {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets {
  __typename: "Asset";
  key: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets_key;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  rootRunId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string | null;
  mode: string;
  canTerminate: boolean;
  tags: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_tags[];
  status: PipelineRunStatus;
  repositoryOrigin: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_repositoryOrigin | null;
  stats: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats;
  assets: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
}

export type PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PythonError | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats_PipelineRunStatsSnapshot;

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns {
  __typename: "PipelineRun";
  id: string;
  stats: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns_stats;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  runsCount: number;
  lastRuns: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_lastRuns[];
  runs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs[];
  status: JobStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks_results[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  scheduleState: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState;
  futureTicks: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_futureTicks;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
}

export type PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PythonError | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats_PipelineRunStatsSnapshot;

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns {
  __typename: "PipelineRun";
  id: string;
  stats: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns_stats;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState {
  __typename: "JobState";
  id: string;
  runsCount: number;
  lastRuns: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_lastRuns[];
  runs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState_runs[];
  status: JobStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  sensorState: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_sensorState;
  nextTick: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors_nextTick | null;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  description: string | null;
  solidHandles: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
  runs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs[];
  schedules: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules[];
  sensors: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_sensors[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError";
  message: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type PipelineOverviewQuery_pipelineSnapshotOrError = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineNotFoundError | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | PipelineOverviewQuery_pipelineSnapshotOrError_PythonError;

export interface PipelineOverviewQuery {
  pipelineSnapshotOrError: PipelineOverviewQuery_pipelineSnapshotOrError;
}

export interface PipelineOverviewQueryVariables {
  pipelineSelector: PipelineSelector;
  limit: number;
}
