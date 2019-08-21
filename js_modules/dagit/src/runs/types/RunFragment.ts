// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, ObjectStoreOperationType, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunFragment
// ====================================================

export interface RunFragment_pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunFragment_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunFragment_pipeline_solids[];
}

export interface RunFragment_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface RunFragment_logs_nodes_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_ExecutionStepSkippedEvent_step | null;
}

export interface RunFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface RunFragment_logs_nodes_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface RunFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries = RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry;

export interface RunFragment_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: RunFragment_logs_nodes_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface RunFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_StepMaterializationEvent_step | null;
  materialization: RunFragment_logs_nodes_StepMaterializationEvent_materialization;
}

export interface RunFragment_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface RunFragment_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_PipelineInitFailureEvent_step | null;
  error: RunFragment_logs_nodes_PipelineInitFailureEvent_error;
}

export interface RunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface RunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: RunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries = RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry;

export interface RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunFragment_logs_nodes_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: RunFragment_logs_nodes_ExecutionStepInputEvent_typeCheck;
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry;

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunFragment_logs_nodes_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: RunFragment_logs_nodes_ExecutionStepOutputEvent_typeCheck;
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries = RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry;

export interface RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunFragment_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_StepExpectationResultEvent_step | null;
  expectationResult: RunFragment_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries = RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry;

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunFragment_logs_nodes_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunFragment_logs_nodes_ObjectStoreOperationEvent_step | null;
  operationResult: RunFragment_logs_nodes_ObjectStoreOperationEvent_operationResult;
}

export type RunFragment_logs_nodes = RunFragment_logs_nodes_ExecutionStepSkippedEvent | RunFragment_logs_nodes_PipelineProcessStartedEvent | RunFragment_logs_nodes_PipelineProcessStartEvent | RunFragment_logs_nodes_StepMaterializationEvent | RunFragment_logs_nodes_PipelineInitFailureEvent | RunFragment_logs_nodes_ExecutionStepFailureEvent | RunFragment_logs_nodes_ExecutionStepInputEvent | RunFragment_logs_nodes_ExecutionStepOutputEvent | RunFragment_logs_nodes_StepExpectationResultEvent | RunFragment_logs_nodes_ObjectStoreOperationEvent;

export interface RunFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: RunFragment_logs_pageInfo;
  nodes: RunFragment_logs_nodes[];
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: RunFragment_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: RunFragment_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface RunFragment_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunFragment_executionPlan_steps_inputs_dependsOn[];
}

export interface RunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunFragment_executionPlan_steps_inputs[];
}

export interface RunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunFragment_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface RunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: RunFragment_pipeline;
  logs: RunFragment_logs;
  environmentConfigYaml: string;
  mode: string;
  executionPlan: RunFragment_executionPlan;
  stepKeysToExecute: (string | null)[] | null;
}
