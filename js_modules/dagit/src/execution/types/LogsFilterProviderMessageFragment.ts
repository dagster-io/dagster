/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsFilterProviderMessageFragment
// ====================================================

export interface LogsFilterProviderMessageFragment {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent" | "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}
