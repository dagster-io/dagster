/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LogsFilterProviderMessageFragment
// ====================================================

export interface LogsFilterProviderMessageFragment_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface LogsFilterProviderMessageFragment {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepFailureEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent" | "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: string;
  step: LogsFilterProviderMessageFragment_step | null;
}
