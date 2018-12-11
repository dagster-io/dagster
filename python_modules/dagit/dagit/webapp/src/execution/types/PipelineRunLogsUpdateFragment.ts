

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunLogsUpdateFragment
// ====================================================

export interface PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineRunLogsUpdateFragment_logs_nodes = PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent;

export interface PipelineRunLogsUpdateFragment_logs {
  nodes: PipelineRunLogsUpdateFragment_logs_nodes[];
}

export interface PipelineRunLogsUpdateFragment {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineRunLogsUpdateFragment_logs;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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
  JOIN = "JOIN",
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