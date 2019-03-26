/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineRunEventFragment
// ====================================================

export interface PipelineExecutionPipelineRunEventFragment_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunEventFragment_LogMessageEvent_step | null;
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
  step: PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_step | null;
  error: PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionPipelineRunEventFragment_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunEventFragment_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineExecutionPipelineRunEventFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunEventFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunEventFragment_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type PipelineExecutionPipelineRunEventFragment = PipelineExecutionPipelineRunEventFragment_LogMessageEvent | PipelineExecutionPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineExecutionPipelineRunEventFragment_PipelineProcessStartedEvent | PipelineExecutionPipelineRunEventFragment_StepMaterializationEvent;
