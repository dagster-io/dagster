

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunExecutionPlanPipelineRunEventFragment
// ====================================================

export interface PipelineRunExecutionPlanPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
  timestamp: string;
}

export interface PipelineRunExecutionPlanPipelineRunEventFragment_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelineRunExecutionPlanPipelineRunEventFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  step: PipelineRunExecutionPlanPipelineRunEventFragment_ExecutionStepStartEvent_step;
}

export type PipelineRunExecutionPlanPipelineRunEventFragment = PipelineRunExecutionPlanPipelineRunEventFragment_LogMessageEvent | PipelineRunExecutionPlanPipelineRunEventFragment_ExecutionStepStartEvent;

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