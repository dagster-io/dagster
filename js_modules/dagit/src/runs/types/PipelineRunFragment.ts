/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunFragment
// ====================================================

export interface PipelineRunFragment_pipeline_solids_definition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineRunFragment_pipeline_solids_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineRunFragment_pipeline_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineRunFragment_pipeline_solids_definition_configDefinition_configType;
}

export interface PipelineRunFragment_pipeline_solids_definition {
  __typename: "SolidDefinition";
  metadata: PipelineRunFragment_pipeline_solids_definition_metadata[];
  configDefinition: PipelineRunFragment_pipeline_solids_definition_configDefinition | null;
}

export interface PipelineRunFragment_pipeline_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineRunFragment_pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineRunFragment_pipeline_solids_inputs_definition_type;
}

export interface PipelineRunFragment_pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineRunFragment_pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineRunFragment_pipeline_solids_inputs_dependsOn_definition_type;
}

export interface PipelineRunFragment_pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunFragment_pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineRunFragment_pipeline_solids_inputs_dependsOn_definition;
  solid: PipelineRunFragment_pipeline_solids_inputs_dependsOn_solid;
}

export interface PipelineRunFragment_pipeline_solids_inputs {
  __typename: "Input";
  definition: PipelineRunFragment_pipeline_solids_inputs_definition;
  dependsOn: PipelineRunFragment_pipeline_solids_inputs_dependsOn | null;
}

export interface PipelineRunFragment_pipeline_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineRunFragment_pipeline_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineRunFragment_pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineRunFragment_pipeline_solids_outputs_definition_type;
  expectations: PipelineRunFragment_pipeline_solids_outputs_definition_expectations[];
}

export interface PipelineRunFragment_pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunFragment_pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineRunFragment_pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineRunFragment_pipeline_solids_outputs_dependedBy_definition_type;
}

export interface PipelineRunFragment_pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineRunFragment_pipeline_solids_outputs_dependedBy_solid;
  definition: PipelineRunFragment_pipeline_solids_outputs_dependedBy_definition;
}

export interface PipelineRunFragment_pipeline_solids_outputs {
  __typename: "Output";
  definition: PipelineRunFragment_pipeline_solids_outputs_definition;
  dependedBy: PipelineRunFragment_pipeline_solids_outputs_dependedBy[];
}

export interface PipelineRunFragment_pipeline_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineRunFragment_pipeline_solids_definition;
  inputs: PipelineRunFragment_pipeline_solids_inputs[];
  outputs: PipelineRunFragment_pipeline_solids_outputs[];
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

export interface PipelineRunFragment_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunFragment_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
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
  name: string;
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

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunFragment_logs_nodes_StepMaterializationEvent_materialization;
}

export type PipelineRunFragment_logs_nodes = PipelineRunFragment_logs_nodes_LogMessageEvent | PipelineRunFragment_logs_nodes_PipelineInitFailureEvent | PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunFragment_logs_nodes_StepMaterializationEvent;

export interface PipelineRunFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunFragment_logs_pageInfo;
  nodes: PipelineRunFragment_logs_nodes[];
}

export interface PipelineRunFragment_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
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
  dependsOn: PipelineRunFragment_executionPlan_steps_inputs_dependsOn;
}

export interface PipelineRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunFragment_executionPlan_steps_solid;
  kind: StepKind;
  key: string;
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
  config: string;
  solidSubset: string[] | null;
  startedAt: string;
  executionPlan: PipelineRunFragment_executionPlan;
}
