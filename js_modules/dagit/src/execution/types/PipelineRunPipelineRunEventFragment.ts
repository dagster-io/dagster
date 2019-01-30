/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunPipelineRunEventFragment
// ====================================================

export interface PipelineRunPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
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

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent_step;
}

export type PipelineRunPipelineRunEventFragment = PipelineRunPipelineRunEventFragment_LogMessageEvent | PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent | PipelineRunPipelineRunEventFragment_ExecutionStepStartEvent;
