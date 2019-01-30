

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExecutionRootQuery
// ====================================================

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_PipelineProcessStartedEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "PipelineProcessStartedEvent";
  processId: number;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionRootQuery_pipeline_runs_logs_nodes = PipelineExecutionRootQuery_pipeline_runs_logs_nodes_LogMessageEvent | PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionRootQuery_pipeline_runs_logs_nodes_PipelineProcessStartedEvent | PipelineExecutionRootQuery_pipeline_runs_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionRootQuery_pipeline_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineExecutionRootQuery_pipeline_runs_logs {
  nodes: PipelineExecutionRootQuery_pipeline_runs_logs_nodes[];
  pageInfo: PipelineExecutionRootQuery_pipeline_runs_logs_pageInfo;
}

export interface PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps {
  name: string;
  solid: PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineExecutionRootQuery_pipeline_runs_executionPlan {
  steps: PipelineExecutionRootQuery_pipeline_runs_executionPlan_steps[];
}

export interface PipelineExecutionRootQuery_pipeline_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionRootQuery_pipeline_runs_logs;
  executionPlan: PipelineExecutionRootQuery_pipeline_runs_executionPlan;
}

export interface PipelineExecutionRootQuery_pipeline_environmentType {
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_RegularConfigType {
  __typename: "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  values: PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType_values[];
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  key: string;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  ofType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType = PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields {
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionRootQuery_pipeline_configTypes = PipelineExecutionRootQuery_pipeline_configTypes_RegularConfigType | PipelineExecutionRootQuery_pipeline_configTypes_EnumConfigType | PipelineExecutionRootQuery_pipeline_configTypes_CompositeConfigType;

export interface PipelineExecutionRootQuery_pipeline {
  name: string;
  runs: PipelineExecutionRootQuery_pipeline_runs[];
  environmentType: PipelineExecutionRootQuery_pipeline_environmentType;
  configTypes: PipelineExecutionRootQuery_pipeline_configTypes[];
}

export interface PipelineExecutionRootQuery {
  pipeline: PipelineExecutionRootQuery_pipeline;
}

export interface PipelineExecutionRootQueryVariables {
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

export enum StepKind {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================