// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunLogsUpdateFragment
// ====================================================

export interface PipelineRunLogsUpdateFragment_pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: PipelineRunLogsUpdateFragment_pipeline_solids[];
}

export interface PipelineRunLogsUpdateFragment_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepSkippedEvent_step | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries = PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent_step | null;
  error: PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent_error;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_step_inputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_step_inputs {
  __typename: "ExecutionStepInput";
  name: string;
  type: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_step_inputs_type;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  inputs: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_step_inputs[];
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries = PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent_typeCheck;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs_type;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs[];
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries = PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries = PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunLogsUpdateFragment_logs_nodes = PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepSkippedEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartEvent | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepInputEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepOutputEvent | PipelineRunLogsUpdateFragment_logs_nodes_StepExpectationResultEvent;

export interface PipelineRunLogsUpdateFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunLogsUpdateFragment_logs_pageInfo;
  nodes: PipelineRunLogsUpdateFragment_logs_nodes[];
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn | null;
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: PipelineRunLogsUpdateFragment_executionPlan_steps_inputs[];
}

export interface PipelineRunLogsUpdateFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunLogsUpdateFragment_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface PipelineRunLogsUpdateFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: PipelineRunLogsUpdateFragment_pipeline;
  logs: PipelineRunLogsUpdateFragment_logs;
  environmentConfigYaml: string;
  mode: string;
  executionPlan: PipelineRunLogsUpdateFragment_executionPlan;
  stepKeysToExecute: (string | null)[] | null;
}
