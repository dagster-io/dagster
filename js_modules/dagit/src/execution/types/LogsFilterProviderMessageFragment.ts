/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsFilterProviderMessageFragment
// ====================================================

export interface LogsFilterProviderMessageFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface LogsFilterProviderMessageFragment_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface LogsFilterProviderMessageFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepFailureEvent" | "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsFilterProviderMessageFragment_ExecutionStepStartEvent_step;
}

export type LogsFilterProviderMessageFragment = LogsFilterProviderMessageFragment_LogMessageEvent | LogsFilterProviderMessageFragment_ExecutionStepStartEvent;
