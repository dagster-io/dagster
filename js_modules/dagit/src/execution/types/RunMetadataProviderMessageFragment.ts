/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunMetadataProviderMessageFragment
// ====================================================

export interface RunMetadataProviderMessageFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  processId: number;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_StepMaterializationEvent_step;
  fileLocation: string | null;
  fileName: string | null;
}

export interface RunMetadataProviderMessageFragment_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunMetadataProviderMessageFragment_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_ExecutionStepStartEvent_step;
}

export type RunMetadataProviderMessageFragment = RunMetadataProviderMessageFragment_LogMessageEvent | RunMetadataProviderMessageFragment_PipelineProcessStartedEvent | RunMetadataProviderMessageFragment_StepMaterializationEvent | RunMetadataProviderMessageFragment_ExecutionStepStartEvent;
