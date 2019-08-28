// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, ObjectStoreOperationType, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunRootQuery
// ====================================================

export interface RunRootQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent_step | null;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries = RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step | null;
  materialization: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step | null;
  error: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_error;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries = RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent_typeCheck;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent_typeCheck;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries = RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_step | null;
  expectationResult: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdString: string;
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries = RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_step | null;
  operationResult: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent_operationResult;
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes = RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepSkippedEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepInputEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepOutputEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepExpectationResultEvent | RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ObjectStoreOperationEvent;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_logs {
  __typename: "LogMessageConnection";
  pageInfo: RunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo;
  nodes: RunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: RunRootQuery_pipelineRunOrError_PipelineRun_pipeline;
  logs: RunRootQuery_pipelineRunOrError_PipelineRun_logs;
  environmentConfigYaml: string;
  mode: string;
  executionPlan: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan;
  stepKeysToExecute: (string | null)[] | null;
}

export type RunRootQuery_pipelineRunOrError = RunRootQuery_pipelineRunOrError_PipelineRunNotFoundError | RunRootQuery_pipelineRunOrError_PipelineRun;

export interface RunRootQuery {
  pipelineRunOrError: RunRootQuery_pipelineRunOrError;
}

export interface RunRootQueryVariables {
  runId: string;
}
