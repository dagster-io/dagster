// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunMetadataProviderMessageFragment
// ====================================================

export interface RunMetadataProviderMessageFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunMetadataProviderMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_ExecutionStepFailureEvent_step | null;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunMetadataProviderMessageFragment_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries = RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry;

export interface RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: RunMetadataProviderMessageFragment_StepMaterializationEvent_materialization_metadataEntries[];
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
  key: string;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries = RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry;

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunMetadataProviderMessageFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  step: RunMetadataProviderMessageFragment_StepExpectationResultEvent_step | null;
  expectationResult: RunMetadataProviderMessageFragment_StepExpectationResultEvent_expectationResult;
}

export type RunMetadataProviderMessageFragment = RunMetadataProviderMessageFragment_ExecutionStepFailureEvent | RunMetadataProviderMessageFragment_PipelineProcessStartedEvent | RunMetadataProviderMessageFragment_PipelineProcessStartEvent | RunMetadataProviderMessageFragment_StepMaterializationEvent | RunMetadataProviderMessageFragment_StepExpectationResultEvent;
