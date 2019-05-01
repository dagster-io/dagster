/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunLogsUpdateFragment
// ====================================================

export interface PipelineRunLogsUpdateFragment_pipeline_solids_definition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineRunLogsUpdateFragment_pipeline_solids_definition_configDefinition_configType;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_definition {
  __typename: "SolidDefinition";
  metadata: PipelineRunLogsUpdateFragment_pipeline_solids_definition_metadata[];
  configDefinition: PipelineRunLogsUpdateFragment_pipeline_solids_definition_configDefinition | null;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineRunLogsUpdateFragment_pipeline_solids_inputs_definition_type;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn_definition_type;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn_definition;
  solid: PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn_solid;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_inputs {
  __typename: "Input";
  definition: PipelineRunLogsUpdateFragment_pipeline_solids_inputs_definition;
  dependsOn: PipelineRunLogsUpdateFragment_pipeline_solids_inputs_dependsOn | null;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_definition_type;
  expectations: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_definition_expectations[];
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy_definition_type;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy_solid;
  definition: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy_definition;
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids_outputs {
  __typename: "Output";
  definition: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_definition;
  dependedBy: PipelineRunLogsUpdateFragment_pipeline_solids_outputs_dependedBy[];
}

export interface PipelineRunLogsUpdateFragment_pipeline_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineRunLogsUpdateFragment_pipeline_solids_definition;
  inputs: PipelineRunLogsUpdateFragment_pipeline_solids_inputs[];
  outputs: PipelineRunLogsUpdateFragment_pipeline_solids_outputs[];
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

export interface PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
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
  name: string;
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

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_materialization;
}

export type PipelineRunLogsUpdateFragment_logs_nodes = PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineInitFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent;

export interface PipelineRunLogsUpdateFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunLogsUpdateFragment_logs_pageInfo;
  nodes: PipelineRunLogsUpdateFragment_logs_nodes[];
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
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
  dependsOn: PipelineRunLogsUpdateFragment_executionPlan_steps_inputs_dependsOn;
}

export interface PipelineRunLogsUpdateFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunLogsUpdateFragment_executionPlan_steps_solid;
  kind: StepKind;
  key: string;
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
  config: string;
  solidSubset: string[] | null;
  startedAt: string;
  executionPlan: PipelineRunLogsUpdateFragment_executionPlan;
}
