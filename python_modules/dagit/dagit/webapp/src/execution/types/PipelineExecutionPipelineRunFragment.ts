

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineRunFragment
// ====================================================

export interface PipelineExecutionPipelineRunFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionPipelineRunFragment_logs_nodes = PipelineExecutionPipelineRunFragment_logs_nodes_LogMessageEvent | PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionPipelineRunFragment_logs {
  nodes: PipelineExecutionPipelineRunFragment_logs_nodes[];
}

export interface PipelineExecutionPipelineRunFragment_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_executionPlan_steps {
  name: string;
  solid: PipelineExecutionPipelineRunFragment_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineExecutionPipelineRunFragment_executionPlan {
  steps: PipelineExecutionPipelineRunFragment_executionPlan_steps[];
}

export interface PipelineExecutionPipelineRunFragment {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionPipelineRunFragment_logs;
  executionPlan: PipelineExecutionPipelineRunFragment_executionPlan;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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
  JOIN = "JOIN",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
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