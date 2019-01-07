

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: PipelineRunLogsSubscription
// ====================================================

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent_run {
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent {
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent_run;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_run {
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent {
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_run;
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_step;
  error: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_run {
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent {
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_run;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_step;
}

export type PipelineRunLogsSubscription_pipelineRunLogs_messages = PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent | PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent | PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent;

export interface PipelineRunLogsSubscription_pipelineRunLogs {
  messages: PipelineRunLogsSubscription_pipelineRunLogs_messages[];
}

export interface PipelineRunLogsSubscription {
  pipelineRunLogs: PipelineRunLogsSubscription_pipelineRunLogs;
}

export interface PipelineRunLogsSubscriptionVariables {
  runId: string;
  after?: any | null;
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