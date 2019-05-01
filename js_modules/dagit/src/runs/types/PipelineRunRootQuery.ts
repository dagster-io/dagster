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

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition_configDefinition_configType;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition {
  __typename: "SolidDefinition";
  metadata: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition_metadata[];
  configDefinition: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition_configDefinition | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_definition_type;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn_definition_type;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn_definition;
  solid: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn_solid;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs {
  __typename: "Input";
  definition: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_definition;
  dependsOn: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs_dependsOn | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_definition_type;
  expectations: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_definition_expectations[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy_definition_type;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy_solid;
  definition: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy_definition;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs {
  __typename: "Output";
  definition: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_definition;
  dependedBy: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs_dependedBy[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_definition;
  inputs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_inputs[];
  outputs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_pipeline_solids_outputs[];
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

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
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
  name: string;
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

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step | null;
  materialization: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_materialization;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo;
  nodes: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
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
  dependsOn: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_solid;
  kind: StepKind;
  key: string;
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
  config: string;
  solidSubset: string[] | null;
  startedAt: string;
  executionPlan: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan;
}

export type PipelineRunRootQuery_pipelineRunOrError = PipelineRunRootQuery_pipelineRunOrError_PipelineRunNotFoundError | PipelineRunRootQuery_pipelineRunOrError_PipelineRun;

export interface PipelineRunRootQuery {
  pipelineRunOrError: PipelineRunRootQuery_pipelineRunOrError;
}

export interface PipelineRunRootQueryVariables {
  runId: string;
}
