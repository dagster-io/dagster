/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineExecutionContainerFragment
// ====================================================

export interface PipelineExecutionContainerFragment_runs_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionContainerFragment_runs_logs_nodes_StepMaterializationEvent_step;
  fileLocation: string;
  fileName: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export type PipelineExecutionContainerFragment_runs_logs_nodes = PipelineExecutionContainerFragment_runs_logs_nodes_LogMessageEvent | PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent | PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionContainerFragment_runs_logs_nodes_StepMaterializationEvent | PipelineExecutionContainerFragment_runs_logs_nodes_PipelineProcessStartedEvent;

export interface PipelineExecutionContainerFragment_runs_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineExecutionContainerFragment_runs_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineExecutionContainerFragment_runs_logs_nodes[];
  pageInfo: PipelineExecutionContainerFragment_runs_logs_pageInfo;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineExecutionContainerFragment_runs_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineExecutionContainerFragment_runs_executionPlan_steps[];
}

export interface PipelineExecutionContainerFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionContainerFragment_runs_logs;
  executionPlan: PipelineExecutionContainerFragment_runs_executionPlan;
}

export interface PipelineExecutionContainerFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionContainerFragment_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionContainerFragment_configTypes_EnumConfigType_values[];
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  ofType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes = PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes_ListConfigType;

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes[];
  ofType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType = PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionContainerFragment_configTypes = PipelineExecutionContainerFragment_configTypes_RegularConfigType | PipelineExecutionContainerFragment_configTypes_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment {
  __typename: "Pipeline";
  name: string;
  runs: PipelineExecutionContainerFragment_runs[];
  environmentType: PipelineExecutionContainerFragment_environmentType;
  configTypes: PipelineExecutionContainerFragment_configTypes[];
}
