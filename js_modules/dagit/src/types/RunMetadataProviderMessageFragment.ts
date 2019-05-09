// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunMetadataProviderMessageFragment
// ====================================================

export interface RunMetadataProviderMessageFragment_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunMetadataProviderMessageFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepFailureEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_LogMessageEvent_step | null;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_StepMaterializationEvent_step | null;
  materialization: RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  name: string | null;
  resultMetadataJsonString: string | null;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_StepExpectationResultEvent_step | null;
  expectationResult: RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult;
}

export type RunMetadataProviderMessageFragment = RunMetadataProviderMessageFragment_LogMessageEvent | RunMetadataProviderMessageFragment_PipelineProcessStartedEvent | RunMetadataProviderMessageFragment_StepMaterializationEvent | RunMetadataProviderMessageFragment_StepExpectationResultEvent;
