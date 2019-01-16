

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
  name: string;
}

export interface PipelineExecutionContainerFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
  isSelector: boolean;
}

export interface PipelineExecutionContainerFragment_types_CompositeType_fields_type {
  name: string;
}

export interface PipelineExecutionContainerFragment_types_CompositeType_fields {
  name: string;
  isOptional: boolean;
  type: PipelineExecutionContainerFragment_types_CompositeType_fields_type;
}

export interface PipelineExecutionContainerFragment_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  isSelector: boolean;
  fields: PipelineExecutionContainerFragment_types_CompositeType_fields[];
}

export type PipelineExecutionContainerFragment_types = PipelineExecutionContainerFragment_types_RegularType | PipelineExecutionContainerFragment_types_CompositeType;

export interface PipelineExecutionContainerFragment_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineExecutionContainerFragment_solids_definition_configDefinition_type {
  name: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_solids_definition_configDefinition {
  type: PipelineExecutionContainerFragment_solids_definition_configDefinition_type;
}

export interface PipelineExecutionContainerFragment_solids_definition {
  metadata: PipelineExecutionContainerFragment_solids_definition_metadata[];
  configDefinition: PipelineExecutionContainerFragment_solids_definition_configDefinition | null;
}

export interface PipelineExecutionContainerFragment_solids_inputs_definition_type {
  name: string;
}

export interface PipelineExecutionContainerFragment_solids_inputs_definition {
  name: string;
  type: PipelineExecutionContainerFragment_solids_inputs_definition_type;
}

export interface PipelineExecutionContainerFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineExecutionContainerFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineExecutionContainerFragment_solids_inputs_dependsOn {
  definition: PipelineExecutionContainerFragment_solids_inputs_dependsOn_definition;
  solid: PipelineExecutionContainerFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineExecutionContainerFragment_solids_inputs {
  definition: PipelineExecutionContainerFragment_solids_inputs_definition;
  dependsOn: PipelineExecutionContainerFragment_solids_inputs_dependsOn | null;
}

export interface PipelineExecutionContainerFragment_solids_outputs_definition_type {
  name: string;
}

export interface PipelineExecutionContainerFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExecutionContainerFragment_solids_outputs_definition {
  name: string;
  type: PipelineExecutionContainerFragment_solids_outputs_definition_type;
  expectations: PipelineExecutionContainerFragment_solids_outputs_definition_expectations[];
}

export interface PipelineExecutionContainerFragment_solids_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineExecutionContainerFragment_solids_outputs_dependedBy {
  solid: PipelineExecutionContainerFragment_solids_outputs_dependedBy_solid;
}

export interface PipelineExecutionContainerFragment_solids_outputs {
  definition: PipelineExecutionContainerFragment_solids_outputs_definition;
  dependedBy: PipelineExecutionContainerFragment_solids_outputs_dependedBy[];
}

export interface PipelineExecutionContainerFragment_solids {
  name: string;
  definition: PipelineExecutionContainerFragment_solids_definition;
  inputs: PipelineExecutionContainerFragment_solids_inputs[];
  outputs: PipelineExecutionContainerFragment_solids_outputs[];
}

export interface PipelineExecutionContainerFragment {
  name: string;
  runs: PipelineExecutionContainerFragment_runs[];
  environmentType: PipelineExecutionContainerFragment_environmentType;
  types: PipelineExecutionContainerFragment_types[];
  solids: PipelineExecutionContainerFragment_solids[];
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