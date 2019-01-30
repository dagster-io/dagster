/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineRunEventFragment
// ====================================================

export interface PipelineExecutionPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
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

export interface PipelineExecutionPipelineRunEventFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent_step;
}

export type PipelineExecutionPipelineRunEventFragment = PipelineExecutionPipelineRunEventFragment_LogMessageEvent | PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineExecutionPipelineRunEventFragment_PipelineProcessStartedEvent | PipelineExecutionPipelineRunEventFragment_ExecutionStepStartEvent;
