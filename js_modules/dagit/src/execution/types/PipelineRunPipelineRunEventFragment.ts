

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunPipelineRunEventFragment
// ====================================================

export interface PipelineRunPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_step;
  error: PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_error;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent_step;
}

export type PipelineRunPipelineRunEventFragment = PipelineRunPipelineRunEventFragment_LogMessageEvent | PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent;

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