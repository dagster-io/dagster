/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsFilterProviderMessageFragment
// ====================================================

export interface LogsFilterProviderMessageFragment_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface LogsFilterProviderMessageFragment {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent" | "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsFilterProviderMessageFragment_step | null;
}
