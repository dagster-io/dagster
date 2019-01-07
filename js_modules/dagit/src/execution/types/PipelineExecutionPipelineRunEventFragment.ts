

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineRunEventFragment
// ====================================================

export interface PipelineExecutionPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_step;
  error: PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent_step;
}

export type PipelineExecutionPipelineRunEventFragment = PipelineExecutionPipelineRunEventFragment_LogMessageEvent | PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent;

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