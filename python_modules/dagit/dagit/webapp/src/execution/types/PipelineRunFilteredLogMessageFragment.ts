

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunFilteredLogMessageFragment
// ====================================================

export interface PipelineRunFilteredLogMessageFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
}

export interface PipelineRunFilteredLogMessageFragment_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelineRunFilteredLogMessageFragment_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelineRunFilteredLogMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  step: PipelineRunFilteredLogMessageFragment_ExecutionStepFailureEvent_step;
  error: PipelineRunFilteredLogMessageFragment_ExecutionStepFailureEvent_error;
}

export type PipelineRunFilteredLogMessageFragment = PipelineRunFilteredLogMessageFragment_LogMessageEvent | PipelineRunFilteredLogMessageFragment_ExecutionStepFailureEvent;

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