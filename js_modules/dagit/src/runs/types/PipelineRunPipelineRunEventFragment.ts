/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunPipelineRunEventFragment
// ====================================================

export interface PipelineRunPipelineRunEventFragment_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_LogMessageEvent_step | null;
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
  step: PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_step | null;
  error: PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_error;
}

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type PipelineRunPipelineRunEventFragment = PipelineRunPipelineRunEventFragment_LogMessageEvent | PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent | PipelineRunPipelineRunEventFragment_StepMaterializationEvent;
