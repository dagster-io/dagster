

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExecutionContainerQuery
// ====================================================

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_PipelineProcessStartedEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "PipelineProcessStartedEvent";
  processId: number;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionContainerQuery_pipeline_runs_logs_nodes = PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_LogMessageEvent | PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_PipelineProcessStartedEvent | PipelineExecutionContainerQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionContainerQuery_pipeline_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_logs {
  nodes: PipelineExecutionContainerQuery_pipeline_runs_logs_nodes[];
  pageInfo: PipelineExecutionContainerQuery_pipeline_runs_logs_pageInfo;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_executionPlan_steps {
  name: string;
  solid: PipelineExecutionContainerQuery_pipeline_runs_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineExecutionContainerQuery_pipeline_runs_executionPlan {
  steps: PipelineExecutionContainerQuery_pipeline_runs_executionPlan_steps[];
}

export interface PipelineExecutionContainerQuery_pipeline_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionContainerQuery_pipeline_runs_logs;
  executionPlan: PipelineExecutionContainerQuery_pipeline_runs_executionPlan;
}

export interface PipelineExecutionContainerQuery_pipeline_environmentType {
  name: string;
}

export interface PipelineExecutionContainerQuery_pipeline_types_RegularType {
  __typename: "RegularType";
  name: string;
  isSelector: boolean;
}

export interface PipelineExecutionContainerQuery_pipeline_types_CompositeType_fields_type {
  name: string;
}

export interface PipelineExecutionContainerQuery_pipeline_types_CompositeType_fields {
  name: string;
  isOptional: boolean;
  type: PipelineExecutionContainerQuery_pipeline_types_CompositeType_fields_type;
}

export interface PipelineExecutionContainerQuery_pipeline_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  isSelector: boolean;
  fields: PipelineExecutionContainerQuery_pipeline_types_CompositeType_fields[];
}

export type PipelineExecutionContainerQuery_pipeline_types = PipelineExecutionContainerQuery_pipeline_types_RegularType | PipelineExecutionContainerQuery_pipeline_types_CompositeType;

export interface PipelineExecutionContainerQuery_pipeline {
  name: string;
  runs: PipelineExecutionContainerQuery_pipeline_runs[];
  environmentType: PipelineExecutionContainerQuery_pipeline_environmentType;
  types: PipelineExecutionContainerQuery_pipeline_types[];
}

export interface PipelineExecutionContainerQuery {
  pipeline: PipelineExecutionContainerQuery_pipeline;
}

export interface PipelineExecutionContainerQueryVariables {
  name: string;
  solidSubset?: string[] | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum EvaluationErrorReason {
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================