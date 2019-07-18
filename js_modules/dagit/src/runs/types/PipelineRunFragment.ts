// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunFragment
// ====================================================

export interface PipelineRunFragment_pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunFragment_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: PipelineRunFragment_pipeline_solids[];
}

export interface PipelineRunFragment_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_ExecutionStepSkippedEvent_step | null;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries = PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_step | null;
  error: PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_error;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_step_inputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_step_inputs {
  __typename: "ExecutionStepInput";
  name: string;
  type: PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_step_inputs_type;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  inputs: PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_step_inputs[];
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries = PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: PipelineRunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs_type;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_step_outputs[];
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries = PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries = PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface PipelineRunFragment_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunFragment_logs_nodes = PipelineRunFragment_logs_nodes_ExecutionStepSkippedEvent | PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunFragment_logs_nodes_PipelineProcessStartEvent | PipelineRunFragment_logs_nodes_StepMaterializationEvent | PipelineRunFragment_logs_nodes_PipelineInitFailureEvent | PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunFragment_logs_nodes_ExecutionStepInputEvent | PipelineRunFragment_logs_nodes_ExecutionStepOutputEvent | PipelineRunFragment_logs_nodes_StepExpectationResultEvent;

export interface PipelineRunFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunFragment_logs_pageInfo;
  nodes: PipelineRunFragment_logs_nodes[];
}

export interface PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface PipelineRunFragment_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunFragment_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface PipelineRunFragment_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: PipelineRunFragment_executionPlan_steps_inputs_dependsOn | null;
}

export interface PipelineRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: PipelineRunFragment_executionPlan_steps_inputs[];
}

export interface PipelineRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunFragment_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface PipelineRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: PipelineRunFragment_pipeline;
  logs: PipelineRunFragment_logs;
  environmentConfigYaml: string;
  mode: string;
  executionPlan: PipelineRunFragment_executionPlan;
  stepKeysToExecute: (string | null)[] | null;
}
