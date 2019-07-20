// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunRootQuery
// ====================================================

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent_step | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step | null;
  error: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_error;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step_inputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step_inputs {
  __typename: "ExecutionStepInput";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step_inputs_type;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  inputs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step_inputs[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step_outputs_type;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step_outputs[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo;
  nodes: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline;
  logs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs;
  environmentConfigYaml: string;
  mode: string;
  executionPlan: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan;
  stepKeysToExecute: (string | null)[] | null;
}

export type PipelineRunRootQuery_pipelineRunOrError = PipelineRunRootQuery_pipelineRunOrError_PipelineRunNotFoundError | PipelineRunRootQuery_pipelineRunOrError_PipelineRun;

export interface PipelineRunRootQuery {
  pipelineRunOrError: PipelineRunRootQuery_pipelineRunOrError;
}

export interface PipelineRunRootQueryVariables {
  runId: string;
}
