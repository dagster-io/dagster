

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerFragment
// ====================================================

export interface PipelineExecutionContainerFragment_runs_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_PipelineProcessStartedEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "PipelineProcessStartedEvent";
  processId: number;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionContainerFragment_runs_logs_nodes = PipelineExecutionContainerFragment_runs_logs_nodes_LogMessageEvent | PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionContainerFragment_runs_logs_nodes_PipelineProcessStartedEvent | PipelineExecutionContainerFragment_runs_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionContainerFragment_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineExecutionContainerFragment_runs_logs {
  nodes: PipelineExecutionContainerFragment_runs_logs_nodes[];
  pageInfo: PipelineExecutionContainerFragment_runs_logs_pageInfo;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan_steps {
  name: string;
  solid: PipelineExecutionContainerFragment_runs_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan {
  steps: PipelineExecutionContainerFragment_runs_executionPlan_steps[];
}

export interface PipelineExecutionContainerFragment_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionContainerFragment_runs_logs;
  executionPlan: PipelineExecutionContainerFragment_runs_executionPlan;
}

export interface PipelineExecutionContainerFragment_environmentType {
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  key: string;
}

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  ofType: PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType = PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionContainerFragment_configTypes_CompositeConfigType_fields {
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

export type PipelineExecutionContainerFragment_configTypes = PipelineExecutionContainerFragment_configTypes_EnumConfigType | PipelineExecutionContainerFragment_configTypes_CompositeConfigType;

export interface PipelineExecutionContainerFragment {
  name: string;
  runs: PipelineExecutionContainerFragment_runs[];
  environmentType: PipelineExecutionContainerFragment_environmentType;
  configTypes: PipelineExecutionContainerFragment_configTypes[];
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