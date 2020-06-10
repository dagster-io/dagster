// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineSelector, PipelineRunStatus, ScheduleTickStatus, ScheduleStatus } from "./../../types/globalTypes";

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
  type: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType" | "ScalarUnionConfigType";
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

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
  solidSelection: string[] | null;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_pipeline_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  name: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string;
}

export type PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_pipeline = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_pipeline_UnknownPipeline | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_pipeline_PipelineSnapshot;

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
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
  runId: string;
  rootRunId: string | null;
  pipeline: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_pipeline;
  mode: string;
  canTerminate: boolean;
  tags: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_tags[];
  status: PipelineRunStatus;
  stats: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_stats;
  assets: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs_assets[];
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_stats_PythonError {
  __typename: "PythonError";
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  endTime: number | null;
}

export type PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_stats = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_stats_PythonError | PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_stats_PipelineRunStatsSnapshot;

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_pipeline;
  tags: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_tags[];
  stats: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs_stats;
  status: PipelineRunStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState {
  __typename: "ScheduleState";
  ticks: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_ticks[];
  runsCount: number;
  runs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_runs[];
  stats: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState_stats;
  ticksCount: number;
  status: ScheduleStatus;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
  scheduleState: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules_scheduleState | null;
}

export interface PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  name: string;
  description: string | null;
  solidHandles: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
  runs: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs[];
  schedules: PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules[];
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
